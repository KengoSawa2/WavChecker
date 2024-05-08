# -*- coding: utf-8 -*-
import copy
import os.path

import xxhash
import pprint
import time
import timecode
import subprocess
from logging.handlers import RotatingFileHandler
import logging
import inspect
import re
import sys
import math
from pathlib import Path
import traceback
import datetime
import wave_bwf_rf64


from PySide2.QtCore import QThread
from PySide2.QtCore import QObject
from PySide2.QtCore import QJsonDocument
from PySide2.QtCore import QMutex
from PySide2.QtCore import QFileInfo
from PySide2.QtCore import QStandardPaths
from PySide2.QtCore import QDir
from PySide2 import QtCore

class WavChecker(QThread, QObject):
    __version__ = "1.5.0"

    MODE_INTERLEAVE = "InterLeave"
    MODE_2CH = "2ch(multi mono)"
    MODE_51CH = "5.1ch"
    MODE_8CH_OA = "8ch"
    MODE_MULTIMONO_INTERLEAVE = "MMONO_InterLeave"
    MODE_MULTIMONO_INTERLEAVE_DANIEL = "MMONO_InterLeave_Daniel"
    # V130
    MODE_MUON_CHECK = "MuonCheck"

    MODE_WAVHASHING_SRC = "HASH_SRC"
    MODE_WAVHASHING_ORG = "HASH_ORG"
    # V130
    MODE_WAVHASHING_SRC_MUON = "HASH_SRC_MUON"

    MODE_FFMPEG_INTERLEAVE = "INTERLEAVE_SINGLE"
    MODE_FFMPEG_51ch = "ISOLATE5.1CH"
    MODE_FFMPEG_2ch = "ISOLATE2CH"
    MODE_FFMPEG_8ch_MULTIMONO = "MULTIMONO8CH"
    MODE_FFMPEG_Xch_MULTIMONO = "MULTIMONOXCH"

    # Thread names
    MASTER = "MASTER"  # Master Thread
    SRC_FILE = "SRC_THREAD"  # SRC target THREAD
    ORG_FILE = "ORG_THREAD"  # ORG target THREAD
    L = "L"  # single wav path(mono,Left)
    R = "R"  # single wav path(mono,Right)
    FL = "FL"  # single wav path(mono,Front Left)
    FR = "FR"  # single wav path(mono,Front Right)
    RR = "RR"  # single wav path(mono,Rear Right)
    RL = "RL"  # single wav path(mono,Rear left)
    FC = "FC"  # single wav path(mono,Front Center)
    LFE = "LFE"  # single wav path(mono,LFE)

    MAX_LOGBYTES = 1024 * 1024 * 20  # 1log size = 20MiB
    MAX_LOGCOUNT = 5  # 5 generation = 20MB * 5 = 100MiB
    LOG_FORMATTER = '%(asctime)s,%(levelname)s,%(message)s'

    WavCheckMutex = QMutex()  # Multi Thread Mutex
    INFOBUF = ""  # str. Lock by WavCheckMutex for information and Debug log.
    ERRBUF = ""  # str, Lock by WavCheckMutex for Error log.

    SRCPATHS = []  # SRC QT path or wav path
    ORGPATHS = []  # ORG wav path(s)

    SIG_BEGINTIMER = QtCore.Signal()
    SIG_STOPTIMER = QtCore.Signal()

    LOGPATH = None
    LOGGER = None
    LOGHANDLER = None
    FORMATTER = None

    PROGRESS_MAX_FFMPEG = 0  # ffmpeg command progress MAX(SRC + ORG)
    PROGRESS_FFMPEG_SRC = 0  # ffmpeg command progress (SRC)
    PROGRESS_FFMPEG_ORG = 0  # ffmpeg command progress (ORG)

    PROGRESS_MAX_ORGWAV = 0  # orgwav hash progressmax(max block?)
    PROGRESS_ORGWAV = 0  # orgwav hash progress.(current)

    PROGRESS_MAX_SRCWAV = 0  # srcwav hash progressmax(max block)
    PROGRESS_SRCWAV = 0  # srcwav hash progress.(current)

    STATUSMESSAGE = ""  # mainwindow statusbar output message
    CHECKEDSTATUS = 0  # checked status 0=Success,1=Warning(5sample length detected) 2=Failed

    TEMPDIR = None  # launch yymmdd temporally folder

    FFPROBEPATH = str(Path(sys.argv[0]).parent.absolute()) + "/" + "ffprobe"
    FFMPEGPATH = str(Path(sys.argv[0]).parent.absolute()) + "/" + "ffmpeg"

    OPDICT_SOURCEQTISBASELIGHT = "sourceQTisBaselight"  # Baselight QT metadata
    OPDICT_SOURCEQTISRESOLVE = "sourceQTisResolve"  # Resolve QT metadata
    OPDICT_SOURCEWAVFORCE16BIT = "SRCFORCE16BITWAV"  # source wav force convert to 16bit True or False
    OPDICT_VIDEOHEADSKIPSEC = "VIDEOHEADSKIP_SEC"  # atama skip sec
    OPDICT_VIDEOHONBENSEC = "VIDEOHONBENSKIP_SEC"  # honben sec
    # v140
    OPDICT_VIDEOSRCORGSWAP = "VIDEOSWAPSRCORG"     # swap src <-> org honbensec
    OPDICT_FPS = "FPS"  # source fps(if source is wav,virtual fps 29.974 set)
    OPDICT_STARTTC = "STARTTC"  # Source TC (timecode object)
    # v141
    OPDICT_STARTTCISNONE = "STARTTCISNONE"  # Source TC is none
    OPDICT_SRCDURATION = "SRCDURATION"  # SRC Duration(msec ex: float(8076.068000))
    OPDICT_ORGDURATION = "ORGDURATION"  # ORG Duration(msec ex: float(8076.068000))
    OPDICT_MAXDURATION = "MAXDURATION"  # SRC or ORG longest duration ex: float(8076.068000)
    OPDICT_SRCWAVFILESIZE = "SRCWAVFILESIZE"  # SRC wav file size(for ffmpeg progress predict)
    OPDICT_ORGWAVFILESIZE = "ORGWAVFILESIZE"  # ORG wav file size(for ffmpeg progress predict)
    OPDICT_MINWAVCHNUM = "MINCHNUM"  # wav channel num(mono)
    # v113
    OPDICT_MAXWAVCHNUM = "MAXCHNUM"  # wav channel num(mono)
    OPDICT_CINEXCHECK = "CINEXCHECK"  # cineXtools bug check
    # v130
    OPDICT_SELECTINDEX = "SELECTINDEX" # Interleave select channel


    BASELIGHT_TAGS_AUDIO_HANDLER_NAME = 'Libquicktime Sound Media Handler'  # baselight output QT audio meta marker
    RESOLVE_TAGS_AUDIO_HANDLER_NAME = 'Blackmagic Design DaVinci Resolve'  # Resolve output QT audio meta marker

    REQ_CANCEL = False  # Cancel Request True or False
    ISRUNNING = False  # isRunning ? True or False

    def __init__(self, mainwin, name):

        super(WavChecker, self).__init__()
        self.mainwin = mainwin
        self.res = None
        self.stdout = ""
        self.stderr = ""
        # self.ffprobe_cmdlist_old = [WavChecker.FFPROBEPATH, "-v", "warning", "-i", None, "-show_streams", "-of","json"]
        self.ffprobe_cmdlist = [WavChecker.FFPROBEPATH, "-v", "warning", "-i", None, "-show_streams", "-show_format",
                                "-of", "json"]

        self.ffprobe_streamsdict = []  # ffprobe json dict list(streams)
        self.ffprobe_formatdict = {}  # ffprobe json dict(format)

        # Argument list to be passed to ffmpeg command, None and /tmp/*.wav paths can be changed as needed in the code.
        # Please note that if there is a time specification at the start and end positions, there is also an insert argument

        # Interleave mode (Include mono,2ch,5.1ch...others)
        # v130 channel select add
        self.ffmpeg_single_interleave_cmdlist = [WavChecker.FFMPEGPATH, "-v", "warning", "-guess_layout_max", "0", "-i",
                                                 None, "-y", "-vn", "-map", "0:a:0",
                                                 "-acodec", None, "-stats", "-stats_period", "1", "/tmp/2ch.wav"]


        # 2ch multi mono(Interleave2ch -> mono2ch)
        self.ffmpeg_2ch_multimono_cmdlist = [WavChecker.FFMPEGPATH, "-v", "warning", "-i", None, "-y", "-vn", \
                                             "-acodec", None, "-stats", "-stats_period", "1", \
                                             "-filter_complex", "channelsplit=channel_layout=stereo[FL][FR]",
                                             "-map", "[FL]", "/tmp/FL.wav", "-acodec", None, "-map", "[FR]",
                                             "/tmp/FR.wav"]

        # 5.1ch multi mono(interleave51 -> mono6ch)
        self.ffmpeg_51ch_multimono_cmdlist = [WavChecker.FFMPEGPATH, "-v", "warning", "-i", None, "-y", "-vn",
                                              "-acodec", None, \
                                              "-stats", "-stats_period", "1", \
                                              "-filter_complex",
                                              "channelsplit=channel_layout=5.1[FL][FR][FC][LFE][BL][BR]", \
                                              "-map", "[FL]", "/tmp/FL.wav", "-acodec", None, "-map", "[FR]",
                                              "/tmp/FR.wav", "-acodec", None, \
                                              "-map", "[FC]", "/tmp/FC.wav", "-acodec", None, "-map", "[LFE]",
                                              "/tmp/LFE.wav", "-acodec", None, \
                                              "-map", "[BL]", "/tmp/BL.wav", "-acodec", None, "-map", "[BR]",
                                              "/tmp/BR.wav"]

        # source multi mono mode(2ch multi mono 2ch -> mono 2ch)
        self.ffmpeg_8ch_multimono_cmdlist_2ch = [WavChecker.FFMPEGPATH, "-v", "warning", "-i", None, "-y", "-vn",
                                                 "-acodec", None,
                                                 "-stats", "-stats_period", "1", \
                                                 "-map", "0:a:0", "/tmp/L.wav", "-acodec", None, \
                                                 "-map", "0:a:1", "/tmp/R.wav"]

        # source multi mono mode(8ch multi mono 8ch -> mono 8ch)
        self.ffmpeg_8ch_multimono_cmdlist_8ch = [WavChecker.FFMPEGPATH, "-v", "warning", "-i", None, "-y", "-vn",
                                                 "-acodec", None, \
                                                 "-stats", "-stats_period", "1", \
                                                 "-map", "0:a:0", "/tmp/L.wav", "-acodec", None, "-map", "0:a:1",
                                                 "/tmp/R.wav", "-acodec", None, \
                                                 "-map", "0:a:2", "/tmp/FL.wav", "-acodec", None, "-map", "0:a:3",
                                                 "/tmp/FR.wav", "-acodec", None, \
                                                 "-map", "0:a:4", "/tmp/FC.wav", "-acodec", None, "-map", "0:a:5",
                                                 "/tmp/LFE.wav", "-acodec", None, \
                                                 "-map", "0:a:6", "/tmp/BL.wav", "-acodec", None, "-map", "0:a:7",
                                                 "/tmp/BR.wav"]

        # source multi mono mode(8ch multi mono 2ch -> Interleave 2ch)
        # v110
        self.ffmpeg_8ch_multimono_cmdlist_interleave2ch = [WavChecker.FFMPEGPATH, "-v", "warning", "-i", None, "-y",
                                                           "-vn", "-acodec", None,
                                                           "-stats", "-stats_period", "1",
                                                           "-filter_complex",
                                                           "[0:a:0][0:a:1]join=inputs=2:channel_layout=stereo[a]",
                                                           "-map", "[a]", None]
        # v140
        # org wav skip sec and honben sec wav extract wav2ch(5.1ch) -> wav2ch(5.1ch)
        self.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch = [WavChecker.FFMPEGPATH, "-v", "warning", "-i", None, "-y",
                                                           "-vn", "-acodec", "copy",
                                                           "-stats", "-stats_period", "1", "/tmp/testL.wav",
                                                           "-i", None, "-acodec", "copy" ,"/tmp/testR.wav",
                                                           "-i", None, "-acodec", "copy" ,"/tmp/testRL.wav",
                                                           "-i", None, "-acodec", "copy" ,"/tmp/testRR.wav",
                                                           "-i", None, "-acodec", "copy" ,"/tmp/testFC.wav",
                                                           "-i", None, "-acodec", "copy" ,"/tmp/testLFE.wav"]


        self.mode = None  # QThread::Run() purpose
        self.opdict = {}
        self.name = name  # Thread name
        self.setObjectName(self.name)  # Thread name for debug symbol

        self.orgpathindex = 0  # "0=2ch or 5.1ch[FL] 1=FR 2=FC 3=LFE 4=BL 5=BR
        self.checksums = {}  # for MODE_WAVHASHING,key = 2ch,FL,FR,FC,LFE,BL,BR value=str(xxhash3 str hex)

        self.aformat = ""  # source or org audio codec name = ex:pcm_s24le

        self.checksumframes_org = [[] for _ in range(8)]  # checksum list entry max 8ch=2ch(LR) + 5.1ch
        self.checksumframes_muon = []                     # V130 checksum list for muon check only

        # ex:23.98fps 48khz -> 1frame =  48048sample per entry.
        # ex:24fps 48khz -> 1frame =  48000sample per entry.

        self.lastframe = [[] for _ in range(8)]  # source or org lastframedata(byte)
        self.lastprevframe = [[] for _ in range(8)]  # source or org lastframe prev frame data(byte)
        # ex: checksumframes_org[-2]

        self.work_wavbytelen = 0  # for lastframe check byte len
        # 16bit = 2,24bit= 3,32bit = 4
        self.work_nchannels = 0  # for lastframe check channel(s)
        # Interleave = 2, other = 1(mono)
        self.work_samplerate = 0  # for 44100hz TC check throw...

        self.cinexdiffbytes_head = [[] for _ in range(8)]       # OPDICT_CINEXCHECK cinexbug diffbytes(bytearray) head data
        self.cinexdiffpos_head = [[] for _ in range(8)]         # OPDICT_CINEXCHECK cinexbug diffpos(wave.tell()) head
        self.cinexdiff_frameindex = [[] for _ in range(8)]      # OPDICT_CINEXCHECK cinexbug diffframeno(int frame index) head

        # v122
        self.cinexdiffbytes_tail = [[] for _ in range(8)]  # OPDICT_CINEXCHECK cinexbug diffbytes(bytearray) tail data

    def reset(self):

        self.SRCPATHS.clear()
        self.ORGPATHS.clear()

        self.mode = None
        self.name = ""
        self.orgpathindex = 0
        self.checksums.clear()
        self.aformat = ""
        self.checksumframes_org.clear()
        self.checksumframes_muon.clear() # V130
        self.lastframe.clear()
        self.lastprevframe.clear()

        self.work_wavbytelen = 0
        self.work_nchannels = 0
        self.work_samplerate = 0
        self.cinexdiffbytes_head = [[] for _ in range(8)]
        self.cinexdiffpos_head = [[] for _ in range(8)]
        self.cinexdiff_frameindex = [[] for _ in range(8)]

        # v122
        self.cinexdiffbytes_tail = [[] for _ in range(8)]

        WavChecker.PROGRESS_MAX_FFMPEG = 0
        WavChecker.PROGRESS_FFMPEG_SRC = 0
        WavChecker.PROGRESS_FFMPEG_ORG = 0
        WavChecker.PROGRESS_MAX_ORGWAV = 0
        WavChecker.PROGRESS_ORGWAV = 0
        WavChecker.PROGRESS_MAX_SRCWAV = 0
        WavChecker.PROGRESS_SRCWAV = 0
        WavChecker.STATUSMESSAGE = ""
        WavChecker.CHECKEDSTATUS = 0
        WavChecker.REQ_CANCEL = False
        WavChecker.ISRUNNING = False

    @classmethod
    def logger_init(cls):

        WavChecker.LOGPATH = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation),
                                          "WavChecker")
        WavChecker.LOGGER = logging.getLogger("WavChecker")
        WavChecker.LOGGER.setLevel(logging.DEBUG)

        if not (os.path.exists(WavChecker.LOGPATH)):
            os.mkdir(WavChecker.LOGPATH)

        WavChecker.LOGHANDLER = RotatingFileHandler(
            os.path.join(WavChecker.LOGPATH, "WavChecker" + ".log"),
            maxBytes=WavChecker.MAX_LOGBYTES,
            backupCount=WavChecker.MAX_LOGCOUNT,
            encoding='utf-8')

        WavChecker.FORMATTER = logging.Formatter(WavChecker.LOG_FORMATTER)
        WavChecker.LOGHANDLER.setFormatter(WavChecker.FORMATTER)
        WavChecker.LOGGER.addHandler(WavChecker.LOGHANDLER)

    @classmethod
    def tempfile_init(cls):

        # If there is a previous execution work directory,
        # delete all contents (leave the previous data but erase it before the next execution)
        WavChecker.tempfile_del()

        t_delta = datetime.timedelta(hours=9)
        JST = datetime.timezone(t_delta, 'JST')
        now = datetime.datetime.now(JST)
        datetimestr = now.strftime('%Y%m%d%H%M%S%f')[:-3]

        WavChecker.TEMPDIR = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation),
                                          "WavChecker", datetimestr)
        if not (os.path.exists(WavChecker.TEMPDIR)):
            os.mkdir(WavChecker.TEMPDIR)

    @classmethod
    def tempfile_del(cls):

        # Delete the last used work file and directory
        if WavChecker.TEMPDIR:
            deldir = QDir(WavChecker.TEMPDIR)
            deldir.removeRecursively()

    def run(self):

        try:

            self.__msgandlogging("opdict:" + pprint.pformat(self.opdict))
            self.__msgandlogging("WavChecker " + self.__version__)
            inputpathindex = 0

            if self.mode == self.MODE_INTERLEAVE:

                WavChecker.STATUSMESSAGE = "INTERLEAVE mode processing started."
                self.SIG_BEGINTIMER.emit()

                WavChecker.ISRUNNING = True

                if (QFileInfo(self.SRCPATHS[0]).suffix() == "mov" or QFileInfo(self.SRCPATHS[0]).suffix() == "mxf"):

                    inputpathindex = 6

                    # QT
                    srcffmpegworker = WavChecker(self.mainwin, self.SRC_FILE)
                    srcffmpegworker.SRCPATHS = self.SRCPATHS.copy()
                    srcffmpegworker.opdict = self.opdict.copy()
                    srcffmpegworker.mode = self.MODE_FFMPEG_INTERLEAVE

                    # v130
                    selectchannel = self.opdict.get(self.OPDICT_SELECTINDEX, 0)

                    newchannelstr = srcffmpegworker.ffmpeg_single_interleave_cmdlist[10][:-1] + str(selectchannel)
                    srcffmpegworker.ffmpeg_single_interleave_cmdlist[10] = newchannelstr

                    if srcffmpegworker.opdict.get(self.OPDICT_SOURCEWAVFORCE16BIT):
                        srcffmpegworker.ffmpeg_single_interleave_cmdlist[12] = "pcm_s16le"
                    else:
                        srcffmpegworker.ffmpeg_single_interleave_cmdlist[12] = self.aformat
                    tempwavname = QFileInfo(self.SRCPATHS[0]).fileName() + "_SRC.wav"
                    srcffmpegworker.ffmpeg_single_interleave_cmdlist[-1] = os.path.join(WavChecker.TEMPDIR, tempwavname)

                    # time specification?
                    # honben
                    if srcffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC):
                        # "-t"
                        tail_sssec = srcffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC)
                        # time insert
                        srcffmpegworker.ffmpeg_single_interleave_cmdlist.insert(7, str(tail_sssec))
                        srcffmpegworker.ffmpeg_single_interleave_cmdlist.insert(7, "-t")

                    # head skip
                    if srcffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC):
                        # "-ss"
                        head_sssec = srcffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC)
                        # time insert
                        srcffmpegworker.ffmpeg_single_interleave_cmdlist.insert(5, str(head_sssec))
                        srcffmpegworker.ffmpeg_single_interleave_cmdlist.insert(5, "-ss")

                        inputpathindex += 2

                    srcffmpegworker.ffmpeg_single_interleave_cmdlist[inputpathindex] = srcffmpegworker.SRCPATHS[0]
                    WavChecker.PROGRESS_MAX_FFMPEG += self.opdict[self.OPDICT_SRCWAVFILESIZE]

                else:
                    # wav
                    srcffmpegworker = None

                if (QFileInfo(self.ORGPATHS[0]).suffix() == "mov" or QFileInfo(self.ORGPATHS[0]).suffix() == "mxf"):

                    orgffmpegworker = WavChecker(self.mainwin, self.ORG_FILE)
                    orgffmpegworker.ORGPATHS = self.ORGPATHS.copy()
                    orgffmpegworker.opdict = self.opdict.copy()
                    orgffmpegworker.mode = self.MODE_FFMPEG_INTERLEAVE
                    # v141
                    orgffmpegworker.ffmpeg_single_interleave_cmdlist[12] = self.aformat
                    tempwavname = QFileInfo(self.ORGPATHS[0]).fileName() + "_ORG.wav"
                    orgffmpegworker.ffmpeg_single_interleave_cmdlist[-1] = os.path.join(WavChecker.TEMPDIR, tempwavname)

                    orgffmpegworker.ffmpeg_single_interleave_cmdlist[6] = orgffmpegworker.ORGPATHS[0]
                    WavChecker.PROGRESS_MAX_FFMPEG += self.opdict[self.OPDICT_ORGWAVFILESIZE]

                else:
                    orgffmpegworker = None

                srcwavworker = WavChecker(self.mainwin, self.SRC_FILE)
                srcwavworker.SRCPATH = self.SRCPATHS.copy()
                srcwavworker.opdict = self.opdict.copy()
                srcwavworker.checksums[self.SRC_FILE] = srcwavworker.SRCPATH
                srcwavworker.ORGPATHS = self.ORGPATHS.copy()

                orgwavworker = WavChecker(self.mainwin, self.ORG_FILE)
                orgwavworker.SRCPATH = self.SRCPATHS.copy()
                orgwavworker.opdict = self.opdict.copy()
                orgwavworker.ORGPATHS = self.ORGPATHS.copy()
                orgwavworker.checksums[self.ORG_FILE] = orgwavworker.ORGPATHS

                srcwavworker.mode = self.MODE_WAVHASHING_SRC
                orgwavworker.mode = self.MODE_WAVHASHING_ORG

                orgwavworker.orgpathindex = 0

                # maybe org is shorter than src.
                if orgffmpegworker:
                    orgffmpegworker.start()
                    WavChecker.STATUSMESSAGE = "orgffmpegworker started."
                    self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":orgffmpegworker start()")

                if srcffmpegworker:
                    srcffmpegworker.start()
                    WavChecker.STATUSMESSAGE = "srcffmpegworker started."
                    self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":srcffmpegworker start() command")

                if orgffmpegworker:
                    self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":orgffmpegworker wait() start.")
                    WavChecker.STATUSMESSAGE = "orgffmpegworker process waiting."
                    orgffmpegworker.wait()
                    self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":orgffmpegworker wait() done.")

                    if WavChecker.REQ_CANCEL:
                        self.__msgandlogging(level=logging.ERROR,
                                             msg=str(self.MODE_INTERLEAVE) + ":" + "ffmpeg処理をキャンセルしました.")
                        self.SIG_STOPTIMER.emit()
                        WavChecker.ISRUNNING = False
                        return

                    orgwavworker.ORGPATHS[0] = orgffmpegworker.ffmpeg_single_interleave_cmdlist[-1]

                self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":orgwavworker start()")

                if srcffmpegworker:
                    self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":srcffmpegworker wait() start.")
                    WavChecker.STATUSMESSAGE = "srcffmpegworker process waiting."
                    srcffmpegworker.wait()
                    self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":srcffmpegworker wait() done.")

                    if WavChecker.REQ_CANCEL:
                        self.__msgandlogging(level=logging.ERROR,
                                             msg=str(
                                                 self.MODE_INTERLEAVE) + ":" + "ffmpeg処理をキャンセルしました.")

                        self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":cancelled")
                        self.SIG_STOPTIMER.emit()
                        WavChecker.ISRUNNING = False
                        return

                if srcffmpegworker:
                    srcwavworker.SRCPATHS[0] = srcffmpegworker.ffmpeg_single_interleave_cmdlist[-1]
                else:
                    srcwavworker.SRCPATHS[0] = self.SRCPATHS[0]


                orgwavworker.start()

                # force end ffmpeg progress bar.
                WavChecker.PROGRESS_FFMPEG_ORG = self.opdict.get(WavChecker.OPDICT_ORGWAVFILESIZE, 0)
                WavChecker.PROGRESS_FFMPEG_SRC = self.opdict.get(WavChecker.OPDICT_SRCWAVFILESIZE, 0)

                # v122
                WavChecker.PROGRESS_MAX_FFMPEG = WavChecker.PROGRESS_FFMPEG_ORG + WavChecker.PROGRESS_FFMPEG_SRC

                # v121 wav to wav
                if srcffmpegworker is None and orgffmpegworker is None:
                    # wav and wav
                    WavChecker.PROGRESS_MAX_FFMPEG = 1
                    WavChecker.PROGRESS_FFMPEG_SRC = 1
                    WavChecker.PROGRESS_FFMPEG_ORG = 0

                self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":srcwavworker start.")
                WavChecker.STATUSMESSAGE = "srcwavworker start."
                srcwavworker.start()

                WavChecker.STATUSMESSAGE = "wav checking"

                orgwavworker.wait()
                srcwavworker.wait()

                self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":srcwavworker and orgwavworker wait() done.")

                if WavChecker.REQ_CANCEL:
                    self.__msgandlogging(level=logging.ERROR,
                        msg=str(self.MODE_INTERLEAVE) + "src or org wavチェックをキャンセルしました.")
                    self.SIG_STOPTIMER.emit()
                    WavChecker.ISRUNNING = False
                    return

                if orgwavworker.isFinished() and srcwavworker.isFinished():

                    self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":" + pprint.pformat(orgwavworker.checksums))
                    # srcprintstr = pprint.pformat(srcwavworker.checksums)
                    self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":" + pprint.pformat(srcwavworker.checksums))

                    if orgwavworker.checksums[self.MODE_INTERLEAVE] == srcwavworker.checksums[self.MODE_INTERLEAVE]:
                        self.__msgandlogging(level=logging.INFO,
                                             msg=str(self.MODE_INTERLEAVE) + "インタリーブチェックモード正常終了")
                        WavChecker.CHECKEDSTATUS = 0  # success
                        WavChecker.STATUSMESSAGE = "インタリーブチェックモード正常終了"
                    else:
                        self.__msgandlogging(level=logging.ERROR,
                                             msg=str(self.MODE_INTERLEAVE) + "インタリーブチェックモードエラー終了")
                        WavChecker.STATUSMESSAGE = "インタリーブチェックモードエラー終了"

                        self.work_wavbytelen = srcwavworker.work_wavbytelen
                        self.work_nchannels = srcwavworker.work_nchannels

                        # V141
                        if self.opdict.get(WavChecker.OPDICT_STARTTCISNONE):
                            # display add virtual wav TC message display.
                            # v131a
                            self.__msgandlogging(level=logging.ERROR, msg="仮想TCとして0Hスタート 29.97fpsでTCを表示します。")

                        # check all frame
                        if srcwavworker.work_samplerate == 44100 or orgwavworker.work_samplerate == 44100:
                            self.__msgandlogging(level=logging.ERROR, msg="44.1khzはTC表示はできません！")
                            WavChecker.CHECKEDSTATUS = 2  # failed
                        else:
                            WavChecker.CHECKEDSTATUS = self.__check_allframe2(self.MODE_INTERLEAVE,
                                                                              srcwavworker.checksumframes_org[0],
                                                                              orgwavworker.checksumframes_org[0],
                                                                              srcwavworker.lastframe[0],
                                                                              orgwavworker.lastframe[0],
                                                                              srcwavworker.lastprevframe[0],
                                                                              orgwavworker.lastprevframe[0])

                else:

                    if not orgwavworker.isFinished():
                        self.__msgandlogging(level=logging.ERROR, msg=str(
                            self.MODE_INTERLEAVE) + ":内部エラー:orgwavworkerスレッドが終了していません！")
                    if not srcwavworker.isFinished():
                        self.__msgandlogging(level=logging.ERROR, msg=str(
                            self.MODE_INTERLEAVE) + ":内部エラー:srcwavworkerスレッドが終了していません！")

                    WavChecker.CHECKEDSTATUS = 2  # failed
                    # orgwavworker error?
                    self.__msgandlogging(level=logging.ERROR,
                                         msg=str(self.MODE_INTERLEAVE) + ":" + ":内部エラー:スレッド操作エラー！")

                self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":終了")
                self.SIG_STOPTIMER.emit()
                WavChecker.ISRUNNING = False

            elif self.mode == self.MODE_51CH:

                WavChecker.STATUSMESSAGE = "5.1ch mode processing started."
                self.SIG_BEGINTIMER.emit()
                WavChecker.ISRUNNING = True

                insert_index_ss = 0
                insert_index_t = 0
                srcwavpathlist = []
                # v140
                orgwavpathlist = []

                if (QFileInfo(self.SRCPATHS[0]).suffix() == "mov" or QFileInfo(self.SRCPATHS[0]).suffix() == "mxf"):

                    orgffmpegworker = None

                    # QT
                    srcffmpegworker = WavChecker(self.mainwin, self.SRC_FILE)
                    srcffmpegworker.SRCPATHS = self.SRCPATHS.copy()
                    srcffmpegworker.opdict = self.opdict.copy()
                    srcffmpegworker.mode = self.MODE_FFMPEG_51ch
                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[4] = ""
                    if srcffmpegworker.opdict.get(self.OPDICT_SOURCEWAVFORCE16BIT):

                        self.aformat = "pcm_s16le"
                        srcffmpegworker.aformat = self.aformat
                    else:
                        srcffmpegworker.aformat = self.aformat

                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[8] = self.aformat
                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[16] = os.path.join(WavChecker.TEMPDIR, "FL.wav")
                    srcwavpathlist.append(srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[16])

                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[18] = self.aformat
                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[21] = os.path.join(WavChecker.TEMPDIR, "FR.wav")
                    srcwavpathlist.append(srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[21])

                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[23] = self.aformat
                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[26] = os.path.join(WavChecker.TEMPDIR, "FC.wav")
                    srcwavpathlist.append(srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[26])

                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[28] = self.aformat
                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[31] = os.path.join(WavChecker.TEMPDIR, "LFE.wav")
                    srcwavpathlist.append(srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[31])

                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[33] = self.aformat
                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[36] = os.path.join(WavChecker.TEMPDIR, "BL.wav")
                    srcwavpathlist.append(srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[36])

                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[38] = self.aformat
                    srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[41] = os.path.join(WavChecker.TEMPDIR, "BR.wav")
                    srcwavpathlist.append(srcffmpegworker.ffmpeg_51ch_multimono_cmdlist[41])

                    # v140
                    if not srcffmpegworker.opdict.get(self.OPDICT_VIDEOSRCORGSWAP):

                        # V113
                        # head skip
                        if srcffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC):
                            # "-ss"
                            head_sssec = srcffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC)
                            # time insert
                            srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(14, str(head_sssec))
                            srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(14, "-ss")
                            insert_index_ss += 2

                            srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(19 + insert_index_ss, str(head_sssec))
                            srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(19 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                            srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(24 + insert_index_ss, str(head_sssec))
                            srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(24 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                            srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(29 + insert_index_ss, str(head_sssec))
                            srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(29 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                            srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(34 + insert_index_ss, str(head_sssec))
                            srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(34 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                            srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(39 + insert_index_ss, str(head_sssec))
                            srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(39 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                        # honben
                        if srcffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC):
                            toffset = 0

                            if insert_index_ss == 0:
                                toffset = 2 # without ss option
                            else:
                                toffset = 4 # with ss option

                                # "-t"
                                tail_sssec = srcffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC)

                                srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(14, str(tail_sssec))
                                srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(14, "-t")
                                insert_index_t += toffset

                                srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(insert_index_t + 19, str(tail_sssec))
                                srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(insert_index_t + 19, "-t")
                                insert_index_t += toffset

                                srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(insert_index_t + 24, str(tail_sssec))
                                srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(insert_index_t + 24, "-t")
                                insert_index_t += toffset

                                srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(insert_index_t + 29, str(tail_sssec))
                                srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(insert_index_t + 29, "-t")
                                insert_index_t += toffset

                                srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(insert_index_t + 34, str(tail_sssec))
                                srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(insert_index_t + 34, "-t")
                                insert_index_t += toffset

                                srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(insert_index_t + 39, str(tail_sssec))
                                srcffmpegworker.ffmpeg_51ch_multimono_cmdlist.insert(insert_index_t + 39, "-t")
                                insert_index_t += toffset

                    # v140 src org swap
                    else:
                        # swap src head and honben sec to org wav
                        orgffmpegworker = WavChecker(self.mainwin, self.ORG_FILE)
                        orgffmpegworker.ORGPATHS = self.ORGPATHS.copy()
                        orgffmpegworker.opdict = self.opdict.copy()
                        orgffmpegworker.mode = self.MODE_FFMPEG_51ch

                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[4] = os.path.join(orgffmpegworker.ORGPATHS[0])
                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[12] = os.path.join(WavChecker.TEMPDIR, "FL_ORG.wav")
                        orgwavpathlist.append(orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[12])

                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[14] = os.path.join(orgffmpegworker.ORGPATHS[1])
                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[17] = os.path.join(WavChecker.TEMPDIR, "FR_ORG.wav")
                        orgwavpathlist.append(orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[17])

                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[19] = os.path.join(orgffmpegworker.ORGPATHS[2])
                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[22] = os.path.join(WavChecker.TEMPDIR, "RL_ORG.wav")
                        orgwavpathlist.append(orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[22])

                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[24] = os.path.join(orgffmpegworker.ORGPATHS[3])
                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[27] = os.path.join(WavChecker.TEMPDIR, "RR_ORG.wav")
                        orgwavpathlist.append(orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[27])

                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[29] = os.path.join(orgffmpegworker.ORGPATHS[4])
                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[32] = os.path.join(WavChecker.TEMPDIR, "FC_ORG.wav")
                        orgwavpathlist.append(orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[32])

                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[34] = os.path.join(orgffmpegworker.ORGPATHS[5])
                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[37] = os.path.join(WavChecker.TEMPDIR, "LFE_ORG.wav")
                        orgwavpathlist.append(orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[37])

                        if orgffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC):
                            # "-ss"
                            head_sssec = orgffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC)

                            # time insert
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(12, str(head_sssec))
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(12, "-ss")
                            insert_index_ss += 2

                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(17 + insert_index_ss, str(head_sssec))
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(17 + insert_index_ss, "-ss")
                            insert_index_ss += 2
                            
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(22 + insert_index_ss, str(head_sssec))
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(22 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(27 + insert_index_ss, str(head_sssec))
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(27 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(32 + insert_index_ss, str(head_sssec))
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(32 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(37 + insert_index_ss, str(head_sssec))
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(37 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                        if orgffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC):
                            toffset = 0

                            if insert_index_ss == 0:
                                toffset = 2 # without ss option
                            else:
                                toffset = 4 # with ss option

                                # "-t"
                                tail_sssec = orgffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC)

                                orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(12, str(tail_sssec))
                                orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(12, "-t")
                                insert_index_t += toffset

                                orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(insert_index_t + 17, str(tail_sssec))
                                orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(insert_index_t + 17, "-t")
                                insert_index_t += toffset

                                orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(insert_index_t + 22, str(tail_sssec))
                                orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(insert_index_t + 22, "-t")
                                insert_index_t += toffset

                                orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(insert_index_t + 27, str(tail_sssec))
                                orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(insert_index_t + 27, "-t")
                                insert_index_t += toffset

                                orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(insert_index_t + 32, str(tail_sssec))
                                orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(insert_index_t + 32, "-t")
                                insert_index_t += toffset

                                orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(insert_index_t + 37, str(tail_sssec))
                                orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(insert_index_t + 37, "-t")
                                insert_index_t += toffset

                else:
                    # wav. 5.1ch wav(single) to 6ch mono? ffmpeg?
                    srcffmpegworker = None

                WavChecker.PROGRESS_MAX_FFMPEG += self.opdict[self.OPDICT_SRCWAVFILESIZE]

                srcwavworker = WavChecker(self.mainwin, self.SRC_FILE)
                srcwavworker.SRCPATHS = self.SRCPATHS.copy()
                srcwavworker.opdict = self.opdict.copy()
                srcwavworker.checksums[self.SRC_FILE] = srcwavworker.SRCPATHS
                srcwavworker.ORGPATHS = self.ORGPATHS
                srcwavworker.mode = self.MODE_WAVHASHING_SRC

                orgwavworker = WavChecker(self.mainwin, self.ORG_FILE)
                orgwavworker.SRCPATHS = self.SRCPATHS.copy()
                orgwavworker.opdict = self.opdict.copy()

                # v140
                if orgffmpegworker:
                    orgwavworker.ORGPATHS = orgwavpathlist.copy()
                    orgwavworker.checksums[self.ORG_FILE] = orgwavpathlist.copy()
                else:
                    orgwavworker.ORGPATHS = self.ORGPATHS.copy()
                    orgwavworker.checksums[self.ORG_FILE] = orgwavworker.ORGPATHS

                orgwavworker.mode = self.MODE_WAVHASHING_ORG

                orgwavworker.orgpathindex = 0  # 2ch wav only mono 2ch can't processing

                # v140
                if orgffmpegworker:
                    orgffmpegworker.start()
                    WavChecker.STATUSMESSAGE = "orgffmpegworker started."
                    self.__msgandlogging(str(self.MODE_51CH) + ":orgffmpegworker start() and waitint() ffmpeg command list is below")

                if srcffmpegworker:
                    srcffmpegworker.start()
                    WavChecker.STATUSMESSAGE = "srcffmpegworker started."
                    self.__msgandlogging(str(self.MODE_51CH) + ":srcffmpegworker start() ffmpeg command list is below")

                # v140
                if orgffmpegworker:
                    orgffmpegworker.wait()
                    # orgwavworker.ORGPATHS = ????

                orgwavworker.start()
                self.__msgandlogging(str(self.MODE_51CH) + ":orgwavworker start()")
                WavChecker.STATUSMESSAGE = "orgwavworker started."

                if srcffmpegworker:
                    self.__msgandlogging(str(self.MODE_51CH) + ":srcffmpegworker wait() start.")
                    WavChecker.STATUSMESSAGE = "srcffmpegworker process waiting."
                    srcffmpegworker.wait()
                    self.__msgandlogging(str(self.MODE_51CH) + ":srcffmpegworker wait() done.")

                    if WavChecker.REQ_CANCEL:
                        self.__msgandlogging(level=logging.WARN,
                                             msg=str(self.MODE_51CH) + ":" + "ffmpeg cancel request detected.")

                        self.__msgandlogging(str(self.MODE_51CH) + ":cancelled")
                        self.SIG_STOPTIMER.emit()
                        WavChecker.ISRUNNING = False
                        return

                # check normal exit?

                if srcffmpegworker:
                    # temporary wav check
                    srcwavworker.SRCPATHS.clear()
                    srcwavworker.SRCPATHS.append(srcwavpathlist[0])
                    srcwavworker.SRCPATHS.append(srcwavpathlist[1])
                    srcwavworker.SRCPATHS.append(srcwavpathlist[2])
                    srcwavworker.SRCPATHS.append(srcwavpathlist[3])
                    srcwavworker.SRCPATHS.append(srcwavpathlist[4])
                    srcwavworker.SRCPATHS.append(srcwavpathlist[5])
                else:
                    # wav direct check
                    srcwavworker.SRCPATHS[0] = self.SRCPATH

                self.__msgandlogging(str(self.MODE_FFMPEG_51ch) + ":srcwavworker start.")
                srcwavworker.start()

                WavChecker.STATUSMESSAGE = "wav checking"

                orgwavworker.wait()
                srcwavworker.wait()

                self.__msgandlogging(str(self.MODE_51CH) + ":srcwavworker and orgwavworker wait() done.")

                if WavChecker.REQ_CANCEL:
                    self.__msgandlogging(level=logging.WARN,
                                         msg=str(self.MODE_51CH) + ":" + "ffmpeg cancel request detected.")

                    self.__msgandlogging(level=logging.ERROR,
                                         msg=str(self.MODE_51CH) + "をキャンセルしました")
                    self.SIG_STOPTIMER.emit()
                    WavChecker.ISRUNNING = False
                    return

                if orgwavworker.isFinished() and srcwavworker.isFinished():

                    self.__msgandlogging(str(self.MODE_51CH) + ":" + pprint.pformat(orgwavworker.checksums))
                    # srcprintstr = pprint.pformat(srcwavworker.checksums)
                    self.__msgandlogging(str(self.MODE_51CH) + ":" + pprint.pformat(srcwavworker.checksums))

                    # Roughly judge whether there is an error or not with a single string
                    # that concatenates the hash values of all channels.
                    if orgwavworker.checksums[self.MODE_51CH] == srcwavworker.checksums[self.MODE_51CH]:
                        self.__msgandlogging(level=logging.INFO,
                                             msg=str(self.MODE_51CH) + "正常終了")
                        WavChecker.CHECKEDSTATUS = 0  # success
                        WavChecker.STATUSMESSAGE = "5.1chチェックモード正常終了"
                    else:

                        self.work_wavbytelen = srcwavworker.work_wavbytelen
                        self.work_nchannels = srcwavworker.work_nchannels

                        self.__msgandlogging(level=logging.ERROR,
                                             msg=str(self.MODE_51CH) + "エラー終了.")

                        WavChecker.STATUSMESSAGE = "5.1chチェックモードエラー終了"

                        if srcwavworker.work_samplerate == 44100 or orgwavworker.work_samplerate == 44100:
                            self.__msgandlogging(level=logging.ERROR, msg="44.1khzはTC表示はできません！")
                            WavChecker.CHECKEDSTATUS = 2  # failed
                        else:

                            # FL?
                            if orgwavworker.checksums[WavChecker.FL] != srcwavworker.checksums[WavChecker.FL]:

                                self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_51CH) \
                                                                              + "Front Left チャンネルでエラーを検知しました！ src={0} org={1} 詳細:".format(
                                    srcwavworker.checksums[WavChecker.FL], orgwavworker.checksums[WavChecker.FL]))
                                WavChecker.STATUSMESSAGE += WavChecker.FL + " "

                                curr_retcode = self.__check_allframe2(self.MODE_51CH,
                                                                      srcwavworker.checksumframes_org[0],
                                                                      orgwavworker.checksumframes_org[0],
                                                                      srcwavworker.lastframe[0],
                                                                      orgwavworker.lastframe[0],
                                                                      srcwavworker.lastprevframe[0],
                                                                      orgwavworker.lastprevframe[0])

                                # override total error level
                                if curr_retcode > WavChecker.CHECKEDSTATUS:
                                    WavChecker.CHECKEDSTATUS = curr_retcode

                            # FR ？
                            if orgwavworker.checksums[WavChecker.FR] != srcwavworker.checksums[WavChecker.FR]:
                                self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_51CH) \
                                                                              + "Front Right チャンネルでエラーを検知しました！ src={0} org={1} 詳細:".format(
                                    srcwavworker.checksums[WavChecker.FR], orgwavworker.checksums[WavChecker.FR]))
                                WavChecker.STATUSMESSAGE += WavChecker.FR + " "

                                curr_retcode = self.__check_allframe2(self.MODE_51CH,
                                                                      srcwavworker.checksumframes_org[1],
                                                                      orgwavworker.checksumframes_org[1],
                                                                      srcwavworker.lastframe[1],
                                                                      orgwavworker.lastframe[1],
                                                                      srcwavworker.lastprevframe[1],
                                                                      orgwavworker.lastprevframe[1])

                                # override total error level
                                if curr_retcode > WavChecker.CHECKEDSTATUS:
                                    WavChecker.CHECKEDSTATUS = curr_retcode

                            # FC ?
                            if orgwavworker.checksums[WavChecker.FC] != srcwavworker.checksums[WavChecker.FC]:
                                self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_51CH) \
                                                                              + "Front Center チャンネルでエラーを検知しました！ src={0} org={1} 詳細:".format(
                                    srcwavworker.checksums[WavChecker.FC], orgwavworker.checksums[WavChecker.FC]))
                                WavChecker.STATUSMESSAGE += WavChecker.FC + " "

                                curr_retcode = self.__check_allframe2(self.MODE_51CH,
                                                                      srcwavworker.checksumframes_org[2],
                                                                      orgwavworker.checksumframes_org[2],
                                                                      srcwavworker.lastframe[2],
                                                                      orgwavworker.lastframe[2],
                                                                      srcwavworker.lastprevframe[2],
                                                                      orgwavworker.lastprevframe[2])

                                # override total error level
                                if curr_retcode > WavChecker.CHECKEDSTATUS:
                                    WavChecker.CHECKEDSTATUS = curr_retcode

                            # LFE?
                            if orgwavworker.checksums[WavChecker.LFE] != srcwavworker.checksums[WavChecker.LFE]:
                                self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_51CH) \
                                                                              + "LFE チャンネルでエラーを検知しました！ differed! src={0} org={1} 詳細:".format(
                                    srcwavworker.checksums[WavChecker.LFE], orgwavworker.checksums[WavChecker.LFE]))
                                WavChecker.STATUSMESSAGE += WavChecker.LFE + " "

                                curr_retcode = self.__check_allframe2(self.MODE_51CH,
                                                                      srcwavworker.checksumframes_org[3],
                                                                      orgwavworker.checksumframes_org[3],
                                                                      srcwavworker.lastframe[3],
                                                                      orgwavworker.lastframe[3],
                                                                      srcwavworker.lastprevframe[3],
                                                                      orgwavworker.lastprevframe[3])

                                # override total error level
                                if curr_retcode > WavChecker.CHECKEDSTATUS:
                                    WavChecker.CHECKEDSTATUS = curr_retcode

                            # RL?
                            if orgwavworker.checksums[WavChecker.RL] != srcwavworker.checksums[WavChecker.RL]:
                                self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_51CH) \
                                                                              + "Rear Left チャンネルでエラーを検知しました src={0} org={1} 詳細:".format(
                                    srcwavworker.checksums[WavChecker.RL], orgwavworker.checksums[WavChecker.RL]))
                                WavChecker.STATUSMESSAGE += WavChecker.RL + " "

                                curr_retcode = self.__check_allframe2(self.MODE_51CH,
                                                                      srcwavworker.checksumframes_org[4],
                                                                      orgwavworker.checksumframes_org[4],
                                                                      srcwavworker.lastframe[4],
                                                                      orgwavworker.lastframe[4],
                                                                      srcwavworker.lastprevframe[4],
                                                                      orgwavworker.lastprevframe[4])

                                # override total error level
                                if curr_retcode > WavChecker.CHECKEDSTATUS:
                                    WavChecker.CHECKEDSTATUS = curr_retcode

                            # RR?
                            if orgwavworker.checksums[WavChecker.RR] != srcwavworker.checksums[WavChecker.RR]:
                                self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_51CH) \
                                                                              + "Rear Right チャンネルでエラーを検知しました src={0} org={1} 詳細:".format(
                                    srcwavworker.checksums[WavChecker.RR], orgwavworker.checksums[WavChecker.RR]))
                                WavChecker.STATUSMESSAGE += WavChecker.RR

                                curr_retcode = self.__check_allframe2(self.MODE_51CH,
                                                                      srcwavworker.checksumframes_org[5],
                                                                      orgwavworker.checksumframes_org[5],
                                                                      srcwavworker.lastframe[5],
                                                                      orgwavworker.lastframe[5],
                                                                      srcwavworker.lastprevframe[5],
                                                                      orgwavworker.lastprevframe[5])
                                # override total error level
                                if curr_retcode > WavChecker.CHECKEDSTATUS:
                                    WavChecker.CHECKEDSTATUS = curr_retcode

                    # v113
                    self.SIG_STOPTIMER.emit()
                    WavChecker.ISRUNNING = False

            elif self.mode == self.MODE_8CH_OA:

                WavChecker.STATUSMESSAGE = "8ch OA mode processing started."
                self.SIG_BEGINTIMER.emit()
                WavChecker.ISRUNNING = True

                insert_index_ss = 0
                insert_index_t = 0
                srcwavpathlist = []

                if (QFileInfo(self.SRCPATHS[0]).suffix() == "mov" or QFileInfo(self.SRCPATHS[0]).suffix() == "mxf"):
                    # QT
                    srcffmpegworker = WavChecker(self.mainwin, self.SRC_FILE)
                    srcffmpegworker.SRCPATHS = self.SRCPATHS.copy()
                    srcffmpegworker.opdict = self.opdict.copy()
                    srcffmpegworker.mode = self.MODE_FFMPEG_8ch_MULTIMONO
                    srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[4] = ""
                    srcffmpegworker.ORGPATHS = self.ORGPATHS.copy()

                    wk_cmdlist = None

                    if srcffmpegworker.opdict.get(self.OPDICT_SOURCEWAVFORCE16BIT):
                        self.aformat = "pcm_s16le"
                        srcffmpegworker.aformat = self.aformat
                    else:
                        srcffmpegworker.aformat = self.aformat

                    if len(self.ORGPATHS) == 2:
                        # SAWA kokokara?
                        # L and R (OA 2ch multi mono)
                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_2ch[8] = self.aformat
                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_2ch[14] = os.path.join(WavChecker.TEMPDIR, "L.wav")
                        srcwavpathlist.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_2ch[14])

                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_2ch[16] = self.aformat
                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_2ch[19] = os.path.join(WavChecker.TEMPDIR, "R.wav")
                        srcwavpathlist.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_2ch[19])

                        wk_cmdlist = srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_2ch

                    elif len(self.ORGPATHS) == 8:

                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[8] = self.aformat
                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[14] = os.path.join(WavChecker.TEMPDIR, "L.wav")
                        srcwavpathlist.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[14])

                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[16] = self.aformat
                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[19] = os.path.join(WavChecker.TEMPDIR, "R.wav")
                        srcwavpathlist.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[19])

                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[21] = self.aformat
                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[24] = os.path.join(WavChecker.TEMPDIR,
                                                                                            "FL.wav")
                        srcwavpathlist.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[24])

                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[26] = self.aformat
                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[29] = os.path.join(WavChecker.TEMPDIR,
                                                                                            "FR.wav")
                        srcwavpathlist.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[29])

                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[31] = self.aformat
                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[34] = os.path.join(WavChecker.TEMPDIR,
                                                                                            "FC.wav")
                        srcwavpathlist.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[34])

                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[36] = self.aformat
                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[39] = os.path.join(WavChecker.TEMPDIR,
                                                                                            "LFE.wav")
                        srcwavpathlist.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[39])

                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[41] = self.aformat
                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[44] = os.path.join(WavChecker.TEMPDIR,
                                                                                            "BL.wav")
                        srcwavpathlist.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[44])

                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[46] = self.aformat
                        srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[49] = os.path.join(WavChecker.TEMPDIR,
                                                                                            "BR.wav")
                        srcwavpathlist.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[49])

                        wk_cmdlist = srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch

                    else:
                        self.__msgandlogging(
                            "MODE_8CH_OA:Internal error. invalid channels channelnum = {0}".format(len(self.ORGPATHS)))
                        self.SIG_STOPTIMER.emit()
                        WavChecker.ISRUNNING = False
                        return

                    if srcffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC):
                        # "-ss"
                        head_sssec = srcffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC)
                        # time insert
                        wk_cmdlist.insert(12, str(head_sssec))
                        wk_cmdlist.insert(12, "-ss")
                        insert_index_ss += 2

                        wk_cmdlist.insert(17 + insert_index_ss, str(head_sssec))
                        wk_cmdlist.insert(17 + insert_index_ss, "-ss")
                        insert_index_ss += 2

                        if wk_cmdlist == self.ffmpeg_8ch_multimono_cmdlist_8ch:

                            wk_cmdlist.insert(22 + insert_index_ss, str(head_sssec))
                            wk_cmdlist.insert(22 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                            wk_cmdlist.insert(27 + insert_index_ss, str(head_sssec))
                            wk_cmdlist.insert(27 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                            wk_cmdlist.insert(32 + insert_index_ss, str(head_sssec))
                            wk_cmdlist.insert(32 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                            wk_cmdlist.insert(37 + insert_index_ss, str(head_sssec))
                            wk_cmdlist.insert(37 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                            wk_cmdlist.insert(42 + insert_index_ss, str(head_sssec))
                            wk_cmdlist.insert(42 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                            wk_cmdlist.insert(47 + insert_index_ss, str(head_sssec))
                            wk_cmdlist.insert(47 + insert_index_ss, "-ss")
                            insert_index_ss += 2

                    # honben
                    if srcffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC):
                        toffset = 0

                        if insert_index_ss == 0:
                            toffset = 2 # without ss option
                        else:
                            toffset = 4 # with ss option

                            # "-t"
                            tail_sssec = srcffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC)

                            wk_cmdlist.insert(12, str(tail_sssec))
                            wk_cmdlist.insert(12, "-t")
                            insert_index_t += toffset

                            wk_cmdlist.insert(insert_index_t + 17, str(tail_sssec))
                            wk_cmdlist.insert(insert_index_t + 17, "-t")
                            insert_index_t += toffset

                            if wk_cmdlist == self.ffmpeg_8ch_multimono_cmdlist_8ch:

                                wk_cmdlist.insert(insert_index_t + 22, str(tail_sssec))
                                wk_cmdlist.insert(insert_index_t + 22, "-t")
                                insert_index_t += toffset

                                wk_cmdlist.insert(insert_index_t + 27, str(tail_sssec))
                                wk_cmdlist.insert(insert_index_t + 27, "-t")
                                insert_index_t += toffset

                                wk_cmdlist.insert(insert_index_t + 32, str(tail_sssec))
                                wk_cmdlist.insert(insert_index_t + 32, "-t")
                                insert_index_t += toffset

                                wk_cmdlist.insert(insert_index_t + 37, str(tail_sssec))
                                wk_cmdlist.insert(insert_index_t + 37, "-t")
                                insert_index_t += toffset

                                wk_cmdlist.insert(insert_index_t + 42, str(tail_sssec))
                                wk_cmdlist.insert(insert_index_t + 42, "-t")
                                insert_index_t += toffset

                                wk_cmdlist.insert(insert_index_t + 47, str(tail_sssec))
                                wk_cmdlist.insert(insert_index_t + 47, "-t")
                                insert_index_t += toffset

                else:
                    self.__msgandlogging("MODE_8CH_OA:Internal error. Can't input wav!!.")
                    self.SIG_STOPTIMER.emit()
                    WavChecker.ISRUNNING = False
                    return

                srcwavworker = WavChecker(self.mainwin, self.SRC_FILE)
                srcwavworker.SRCPATHS = self.SRCPATHS.copy()
                srcwavworker.opdict = self.opdict.copy()
                srcwavworker.checksums[self.SRC_FILE] = srcwavworker.SRCPATHS
                srcwavworker.ORGPATHS = self.ORGPATHS

                orgwavworker = WavChecker(self.mainwin, self.ORG_FILE)
                orgwavworker.SRCPATHS = self.SRCPATHS.copy()
                orgwavworker.opdict = self.opdict.copy()
                orgwavworker.ORGPATHS = self.ORGPATHS.copy()
                orgwavworker.checksums[self.ORG_FILE] = orgwavworker.ORGPATHS

                srcwavworker.mode = self.MODE_WAVHASHING_SRC
                orgwavworker.mode = self.MODE_WAVHASHING_ORG

                orgwavworker.orgpathindex = 0  # 2ch wav only mono 2ch can't processing

                WavChecker.PROGRESS_MAX_FFMPEG += self.opdict[self.OPDICT_SRCWAVFILESIZE]

                if srcffmpegworker:
                    srcffmpegworker.start()
                    WavChecker.STATUSMESSAGE = "srcffmpegworker started."
                    self.__msgandlogging(
                        str(self.MODE_8CH_OA) + ":srcffmpegworker start() ffmpeg command list is below")

                # v112
                if not self.opdict.get(WavChecker.OPDICT_CINEXCHECK):
                    # start org wav hashing
                    orgwavworker.start()

                self.__msgandlogging(str(self.MODE_8CH_OA) + ":orgwavworker start()")
                WavChecker.STATUSMESSAGE = "orgwavworker started."

                if srcffmpegworker:
                    self.__msgandlogging(str(self.MODE_8CH_OA) + ":srcffmpegworker wait() start.")
                    WavChecker.STATUSMESSAGE = "srcffmpegworker process waiting."
                    srcffmpegworker.wait()
                    self.__msgandlogging(str(self.MODE_8CH_OA) + ":srcffmpegworker wait() done.")

                    if WavChecker.REQ_CANCEL:
                        self.__msgandlogging(level=logging.WARN,
                                             msg=str(self.MODE_8CH_OA) + ":" + "ffmpeg cancel request detected.")

                        self.__msgandlogging(str(self.MODE_8CH_OA) + ":cancelled")
                        self.SIG_STOPTIMER.emit()
                        WavChecker.ISRUNNING = False
                        return

                # temporary wav check
                srcwavworker.SRCPATHS.clear()

                if len(self.ORGPATHS) == 2:
                    # 2ch
                    srcwavworker.SRCPATHS.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_2ch[14])
                    srcwavworker.SRCPATHS.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_2ch[19])
                else:
                    # 8ch
                    srcwavworker.SRCPATHS.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[14])
                    srcwavworker.SRCPATHS.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[19])
                    srcwavworker.SRCPATHS.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[24])
                    srcwavworker.SRCPATHS.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[29])
                    srcwavworker.SRCPATHS.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[34])
                    srcwavworker.SRCPATHS.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[39])
                    srcwavworker.SRCPATHS.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[44])
                    srcwavworker.SRCPATHS.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch[49])

                # v112 wait for CINEXCHECK wav preprocess required.
                if self.opdict.get(WavChecker.OPDICT_CINEXCHECK):
                    # v112 preprocess wav differ block

                    cmdlist = []
                    cmdindex = 14

                    if len(self.ORGPATHS) == 2:
                        cmdlist = srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_2ch
                    elif len(self.ORGPATHS) == 8:
                        cmdlist = srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_8ch
                    else:
                        self.__msgandlogging("cmdlist selected choice internal error. call sawatsu!!!",
                                             level=logging.ERROR)
                        WavChecker.REQ_CANCEL = True
                        return

                    channelindex = 0
                    for workpath in self.ORGPATHS:

                        wk_tuple = self.preprocess_wav_forcinex(cmdlist[cmdindex],
                                                                workpath,
                                                                0)

                        if wk_tuple:
                            # v122
                            srcwavworker.cinexdiffbytes_head[channelindex] = wk_tuple[0]  # bytesarray (head diff)
                            srcwavworker.cinexdiffpos_head[channelindex] = wk_tuple[1]  # orgindex
                            srcwavworker.cinexdiffbytes_tail[channelindex] = wk_tuple[2]  # bytesarray (tail diff)
                        else:
                            WavChecker.REQ_CANCEL = True
                            break
                        channelindex += 1

                    if WavChecker.REQ_CANCEL:
                        self.__msgandlogging(level=logging.ERROR,
                                             msg=str(self.MODE_8CH_OA) + "src or org wavチェックをキャンセルしました.")
                        WavChecker.STATUSMESSAGE = "cinexズレチェックモードが異常終了しました"
                        self.SIG_STOPTIMER.emit()
                        WavChecker.CHECKEDSTATUS = 1
                        WavChecker.ISRUNNING = False
                        return

                    orgwavworker.start()
                    # v112 kokomade

                self.__msgandlogging(str(self.MODE_8CH_OA) + ":srcwavworker start.")
                srcwavworker.start()

                WavChecker.STATUSMESSAGE = "wav checking"

                orgwavworker.wait()
                srcwavworker.wait()

                self.__msgandlogging(str(self.MODE_8CH_OA) + ":srcwavworker and orgwavworker wait() done.")

                if WavChecker.REQ_CANCEL:
                    self.__msgandlogging(level=logging.WARN,
                                         msg=str(self.MODE_8CH_OA) + ":" + "ffmpeg cancel request detected.")

                    self.__msgandlogging(str(self.MODE_8CH_OA) + ":cancelled")
                    self.SIG_STOPTIMER.emit()
                    WavChecker.ISRUNNING = False
                    return

                if orgwavworker.isFinished() and srcwavworker.isFinished():

                    self.__msgandlogging(str(self.MODE_8CH_OA) + ":" + pprint.pformat(orgwavworker.checksums))
                    self.__msgandlogging(str(self.MODE_8CH_OA) + ":" + pprint.pformat(srcwavworker.checksums))

                    # Roughly judge whether there is an error or not with a single string
                    # that concatenates the hash values of all channels.
                    if orgwavworker.checksums[self.MODE_8CH_OA] == srcwavworker.checksums[self.MODE_8CH_OA]:
                        self.__msgandlogging(level=logging.INFO, msg=str(self.MODE_8CH_OA) + " OAチェックモード正常終了")
                        WavChecker.CHECKEDSTATUS = 0  # success
                        WavChecker.STATUSMESSAGE = "OAチェックモード正常終了"
                    else:

                        self.work_wavbytelen = srcwavworker.work_wavbytelen
                        self.work_nchannels = srcwavworker.work_nchannels

                        self.__msgandlogging(level=logging.ERROR,
                                             msg=str(self.MODE_8CH_OA) + "OAチェックモードエラー終了.\n")

                        WavChecker.STATUSMESSAGE = "OAチェックモードエラー終了"

                        if srcwavworker.work_samplerate == 44100 or orgwavworker.work_samplerate == 44100:
                            self.__msgandlogging(level=logging.ERROR, msg="44.1khzはTC表示はできません！")
                            WavChecker.CHECKEDSTATUS = 2  # failed
                        else:

                            # V112
                            channelindex = 0
                            for workpath in self.ORGPATHS:
                                # V122 kokokara
                                self.cinexdiff_frameindex[channelindex] = srcwavworker.cinexdiff_frameindex[channelindex]
                                self.cinexdiffbytes_head[channelindex] = srcwavworker.cinexdiffbytes_head[channelindex]
                                # V122 kokomade
                                channelindex += 1
                            # V112 kokomade
                            if orgwavworker.checksums[WavChecker.L] != srcwavworker.checksums[WavChecker.L]:

                                self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_8CH_OA) \
                                                                              + "[Left] チャンネルでエラーを検知しました！ src={0} org={1}\n詳細:".format(
                                    srcwavworker.checksums[WavChecker.L], orgwavworker.checksums[WavChecker.L]))
                                WavChecker.STATUSMESSAGE += WavChecker.L + " "

                                curr_retcode = self.__check_allframe2(self.MODE_8CH_OA,
                                                                      srcwavworker.checksumframes_org[0],
                                                                      orgwavworker.checksumframes_org[0],
                                                                      srcwavworker.lastframe[0],
                                                                      orgwavworker.lastframe[0],
                                                                      srcwavworker.lastprevframe[0],
                                                                      orgwavworker.lastprevframe[0],
                                                                      0)

                                # override total error level
                                if curr_retcode > WavChecker.CHECKEDSTATUS:
                                    WavChecker.CHECKEDSTATUS = curr_retcode

                            if orgwavworker.checksums[WavChecker.R] != srcwavworker.checksums[WavChecker.R]:

                                self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_8CH_OA) \
                                                                              + "[Right] チャンネルでエラーを検知しました！ src={0} org={1}\n詳細:".format(
                                    srcwavworker.checksums[WavChecker.R], orgwavworker.checksums[WavChecker.R]))
                                WavChecker.STATUSMESSAGE += WavChecker.R + " "

                                curr_retcode = self.__check_allframe2(self.MODE_8CH_OA,
                                                                      srcwavworker.checksumframes_org[1],
                                                                      orgwavworker.checksumframes_org[1],
                                                                      srcwavworker.lastframe[1],
                                                                      orgwavworker.lastframe[1],
                                                                      srcwavworker.lastprevframe[1],
                                                                      orgwavworker.lastprevframe[1],
                                                                      1)

                                # override total error level
                                if curr_retcode > WavChecker.CHECKEDSTATUS:
                                    WavChecker.CHECKEDSTATUS = curr_retcode

                            if len(self.ORGPATHS) == 8:
                                # FL?
                                if orgwavworker.checksums[WavChecker.FL] != srcwavworker.checksums[WavChecker.FL]:

                                    self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_8CH_OA) \
                                                                                  + "[Front Left] チャンネルでエラーを検知しました！ src={0} org={1}\n詳細:".format(
                                        srcwavworker.checksums[WavChecker.FL], orgwavworker.checksums[WavChecker.FL]))
                                    WavChecker.STATUSMESSAGE += WavChecker.FL + " "

                                    curr_retcode = self.__check_allframe2(self.MODE_8CH_OA,
                                                                          srcwavworker.checksumframes_org[2],
                                                                          orgwavworker.checksumframes_org[2],
                                                                          srcwavworker.lastframe[2],
                                                                          orgwavworker.lastframe[2],
                                                                          srcwavworker.lastprevframe[2],
                                                                          orgwavworker.lastprevframe[2],
                                                                          2)

                                    # override total error level
                                    if curr_retcode > WavChecker.CHECKEDSTATUS:
                                        WavChecker.CHECKEDSTATUS = curr_retcode

                                # FR ？
                                if orgwavworker.checksums[WavChecker.FR] != srcwavworker.checksums[WavChecker.FR]:
                                    self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_8CH_OA) \
                                                                                  + "[Front Right] チャンネルでエラーを検知しました！ src={0} org={1}\n詳細:".format(
                                        srcwavworker.checksums[WavChecker.FR], orgwavworker.checksums[WavChecker.FR]))
                                    WavChecker.STATUSMESSAGE += WavChecker.FR + " "

                                    curr_retcode = self.__check_allframe2(self.MODE_8CH_OA,
                                                                          srcwavworker.checksumframes_org[3],
                                                                          orgwavworker.checksumframes_org[3],
                                                                          srcwavworker.lastframe[3],
                                                                          orgwavworker.lastframe[3],
                                                                          srcwavworker.lastprevframe[3],
                                                                          orgwavworker.lastprevframe[3],
                                                                          3)

                                    # override total error level
                                    if curr_retcode > WavChecker.CHECKEDSTATUS:
                                        WavChecker.CHECKEDSTATUS = curr_retcode

                                # FC ?
                                if orgwavworker.checksums[WavChecker.FC] != srcwavworker.checksums[WavChecker.FC]:
                                    self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_8CH_OA) \
                                                                                  + "[Front Center] チャンネルでエラーを検知しました！ src={0} org={1}\n詳細:".format(
                                        srcwavworker.checksums[WavChecker.FC], orgwavworker.checksums[WavChecker.FC]))
                                    WavChecker.STATUSMESSAGE += WavChecker.FC + " "

                                    curr_retcode = self.__check_allframe2(self.MODE_8CH_OA,
                                                                          srcwavworker.checksumframes_org[4],
                                                                          orgwavworker.checksumframes_org[4],
                                                                          srcwavworker.lastframe[4],
                                                                          orgwavworker.lastframe[4],
                                                                          srcwavworker.lastprevframe[4],
                                                                          orgwavworker.lastprevframe[4],
                                                                          4)

                                    # override total error level
                                    if curr_retcode > WavChecker.CHECKEDSTATUS:
                                        WavChecker.CHECKEDSTATUS = curr_retcode

                                # LFE?
                                if orgwavworker.checksums[WavChecker.LFE] != srcwavworker.checksums[WavChecker.LFE]:
                                    self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_8CH_OA) \
                                                                                  + "[LFE] チャンネルでエラーを検知しました！ differed! src={0} org={1}\n詳細:".format(
                                        srcwavworker.checksums[WavChecker.LFE], orgwavworker.checksums[WavChecker.LFE]))
                                    WavChecker.STATUSMESSAGE += WavChecker.LFE + " "

                                    curr_retcode = self.__check_allframe2(self.MODE_8CH_OA,
                                                                          srcwavworker.checksumframes_org[5],
                                                                          orgwavworker.checksumframes_org[5],
                                                                          srcwavworker.lastframe[5],
                                                                          orgwavworker.lastframe[5],
                                                                          srcwavworker.lastprevframe[5],
                                                                          orgwavworker.lastprevframe[5],
                                                                          5)

                                    # override total error level
                                    if curr_retcode > WavChecker.CHECKEDSTATUS:
                                        WavChecker.CHECKEDSTATUS = curr_retcode

                                # RL?
                                if orgwavworker.checksums[WavChecker.RL] != srcwavworker.checksums[WavChecker.RL]:
                                    self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_8CH_OA) \
                                                                                  + "[Rear Left] チャンネルでエラーを検知しました src={0} org={1}\n詳細:".format(
                                        srcwavworker.checksums[WavChecker.RL], orgwavworker.checksums[WavChecker.RL]))
                                    WavChecker.STATUSMESSAGE += WavChecker.RL + " "

                                    curr_retcode = self.__check_allframe2(self.MODE_51CH,
                                                                          srcwavworker.checksumframes_org[6],
                                                                          orgwavworker.checksumframes_org[6],
                                                                          srcwavworker.lastframe[6],
                                                                          orgwavworker.lastframe[6],
                                                                          srcwavworker.lastprevframe[6],
                                                                          orgwavworker.lastprevframe[6],
                                                                          6)

                                    # override total error level
                                    if curr_retcode > WavChecker.CHECKEDSTATUS:
                                        WavChecker.CHECKEDSTATUS = curr_retcode

                                # RR?
                                if orgwavworker.checksums[WavChecker.RR] != srcwavworker.checksums[WavChecker.RR]:
                                    self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_8CH_OA) \
                                                                                  + "[Rear Right] チャンネルでエラーを検知しました src={0} org={1}\n詳細:".format(
                                        srcwavworker.checksums[WavChecker.RR], orgwavworker.checksums[WavChecker.RR]))
                                    WavChecker.STATUSMESSAGE += WavChecker.RR

                                    curr_retcode = self.__check_allframe2(self.MODE_8CH_OA,
                                                                          srcwavworker.checksumframes_org[7],
                                                                          orgwavworker.checksumframes_org[7],
                                                                          srcwavworker.lastframe[7],
                                                                          orgwavworker.lastframe[7],
                                                                          srcwavworker.lastprevframe[7],
                                                                          orgwavworker.lastprevframe[7],
                                                                          7)
                                    # override total error level
                                    if curr_retcode > WavChecker.CHECKEDSTATUS:
                                        WavChecker.CHECKEDSTATUS = curr_retcode

                else:

                    if not orgwavworker.isFinished():
                        self.__msgandlogging(level=logging.ERROR, msg=str(
                            self.MODE_8CH_OA) + ":内部エラー:orgwavworkerスレッドが終了していません！")
                    if not srcwavworker.isFinished():
                        self.__msgandlogging(level=logging.ERROR, msg=str(
                            self.MODE_8CH_OA) + ":内部エラー:srcwavworkerスレッドが終了していません！")

                    WavChecker.CHECKEDSTATUS = 2  # failed
                    # orgwavworker error?
                    self.__msgandlogging(level=logging.ERROR,
                                         msg=str(self.MODE_8CH_OA) + ":" + ":内部エラー:スレッド操作エラー！")

                self.__msgandlogging(str(self.MODE_8CH_OA) + ":終了")
                self.SIG_STOPTIMER.emit()
                WavChecker.ISRUNNING = False

            elif self.mode == self.MODE_2CH:
                # 2ch (multi mono) mode
                WavChecker.STATUSMESSAGE = "2ch(multi mono) mode processing started."
                self.SIG_BEGINTIMER.emit()

                WavChecker.ISRUNNING = True

                insert_index = 0

                # v141
                orgffmpegworker = None

                # v140
                srcwavpathlist = []
                orgwavpathlist = []

                if (QFileInfo(self.SRCPATHS[0]).suffix() == "mov" or QFileInfo(self.SRCPATHS[0]).suffix() == "mxf"):
                    # QT
                    srcffmpegworker = WavChecker(self.mainwin, self.SRC_FILE)
                    srcffmpegworker.SRCPATHS = self.SRCPATHS.copy()
                    srcffmpegworker.opdict = self.opdict.copy()
                    srcffmpegworker.mode = self.MODE_FFMPEG_2ch
                    srcffmpegworker.ffmpeg_2ch_multimono_cmdlist[4] = ""

                    if srcffmpegworker.opdict.get(self.OPDICT_SOURCEWAVFORCE16BIT):
                        self.aformat = "pcm_s16le"
                        srcffmpegworker.aformat = self.aformat
                    else:
                        srcffmpegworker.aformat = self.aformat
                    srcffmpegworker.ffmpeg_2ch_multimono_cmdlist[8] = self.aformat
                    srcffmpegworker.ffmpeg_2ch_multimono_cmdlist[16] = os.path.join(WavChecker.TEMPDIR, "FL.wav")
                    # V140
                    srcwavpathlist.append(srcffmpegworker.ffmpeg_2ch_multimono_cmdlist[16])
                    srcffmpegworker.ffmpeg_2ch_multimono_cmdlist[18] = self.aformat
                    srcffmpegworker.ffmpeg_2ch_multimono_cmdlist[21] = os.path.join(WavChecker.TEMPDIR, "FR.wav")
                    srcwavpathlist.append(srcffmpegworker.ffmpeg_2ch_multimono_cmdlist[21])

                    # v140
                    if not srcffmpegworker.opdict.get(self.OPDICT_VIDEOSRCORGSWAP):
                        # V113
                        # head skip
                        if srcffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC):
                            # "-ss"
                            head_sssec = srcffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC)
                            # time insert
                            srcffmpegworker.ffmpeg_2ch_multimono_cmdlist.insert(14, str(head_sssec))
                            srcffmpegworker.ffmpeg_2ch_multimono_cmdlist.insert(14, "-ss")
                            insert_index += 2
                            srcffmpegworker.ffmpeg_2ch_multimono_cmdlist.insert(19 + insert_index, str(head_sssec))
                            srcffmpegworker.ffmpeg_2ch_multimono_cmdlist.insert(19 + insert_index, "-ss")

                        # honben
                        if srcffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC):

                            # "-t"
                            tail_sssec = srcffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC)
                            # time insert
                            srcffmpegworker.ffmpeg_2ch_multimono_cmdlist.insert(14, str(tail_sssec))
                            srcffmpegworker.ffmpeg_2ch_multimono_cmdlist.insert(14, "-t")
                            insert_index += 2
                            srcffmpegworker.ffmpeg_2ch_multimono_cmdlist.insert(insert_index + 19, str(tail_sssec))
                            srcffmpegworker.ffmpeg_2ch_multimono_cmdlist.insert(insert_index + 19, "-t")
                    # v140 src org swap
                    else:
                        # swap src head and honben sec to org wav
                        orgffmpegworker = WavChecker(self.mainwin, self.ORG_FILE)
                        orgffmpegworker.ORGPATHS = self.ORGPATHS.copy()
                        orgffmpegworker.opdict = self.opdict.copy()
                        orgffmpegworker.mode = self.MODE_FFMPEG_51ch

                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[4] = os.path.join(orgffmpegworker.ORGPATHS[0])
                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[12] = os.path.join(WavChecker.TEMPDIR, "L_ORG.wav")
                        orgwavpathlist.append(orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[12])

                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[14] = os.path.join(orgffmpegworker.ORGPATHS[1])
                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[17] = os.path.join(WavChecker.TEMPDIR, "R_ORG.wav")
                        orgwavpathlist.append(orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch[17])

                        if orgffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC):
                            # "-ss"
                            head_sssec = orgffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC)

                            # time insert
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(12,
                                                                                                      str(head_sssec))
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(12, "-ss")
                            insert_index += 2

                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(
                                17 + insert_index, str(head_sssec))
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(
                                17 + insert_index, "-ss")
                            insert_index += 2

                        if orgffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC):

                            # "-t"
                            tail_sssec = orgffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC)

                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(12,
                                                                                                      str(tail_sssec))
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(12, "-t")
                            insert_index += 2

                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(
                                insert_index + 17, str(tail_sssec))
                            orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch.insert(
                                insert_index + 17, "-t")
                            insert_index += 2
                        # delete command args above L,R
                        commandlist = orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch
                        commandlist = commandlist[:insert_index + 18]
                        orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch = commandlist.copy()
                        # print(orgffmpegworker.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch)

                else:
                    # Internal error:
                    pass

                srcwavworker = WavChecker(self.mainwin, self.SRC_FILE)
                srcwavworker.SRCPATHS = self.SRCPATHS.copy()
                srcwavworker.opdict = self.opdict.copy()
                srcwavworker.checksums[self.SRC_FILE] = srcwavworker.SRCPATHS
                srcwavworker.ORGPATHS = self.ORGPATHS

                orgwavworker = WavChecker(self.mainwin, self.ORG_FILE)
                orgwavworker.SRCPATHS = self.SRCPATHS.copy()
                orgwavworker.opdict = self.opdict.copy()
                orgwavworker.ORGPATHS = self.ORGPATHS.copy()
                orgwavworker.checksums[self.ORG_FILE] = orgwavworker.ORGPATHS

                # v140
                if orgffmpegworker:
                    orgwavworker.ORGPATHS = orgwavpathlist.copy()
                    orgwavworker.checksums[self.ORG_FILE] = orgwavpathlist.copy()
                else:
                    orgwavworker.ORGPATHS = self.ORGPATHS.copy()
                    orgwavworker.checksums[self.ORG_FILE] = orgwavworker.ORGPATHS


                srcwavworker.mode = self.MODE_WAVHASHING_SRC
                orgwavworker.mode = self.MODE_WAVHASHING_ORG

                orgwavworker.orgpathindex = 0

                WavChecker.PROGRESS_MAX_FFMPEG += self.opdict[self.OPDICT_SRCWAVFILESIZE]

                # v140
                if orgffmpegworker:
                    orgffmpegworker.start()
                    WavChecker.STATUSMESSAGE = "orgffmpegworker started."
                    self.__msgandlogging(str(self.MODE_2CH) + ":orgffmpegworker start() and waitint() ffmpeg command list is below")

                if srcffmpegworker:
                    srcffmpegworker.start()
                    WavChecker.STATUSMESSAGE = "srcffmpegworker started."
                    self.__msgandlogging(str(self.MODE_2CH) + ":srcffmpegworker start() ffmpeg command list is below")

                if orgffmpegworker:
                    orgffmpegworker.wait()

                orgwavworker.start()
                self.__msgandlogging(str(self.MODE_2CH) + ":orgwavworker start()")
                WavChecker.STATUSMESSAGE = "orgwavworker started."

                if srcffmpegworker:
                    self.__msgandlogging(str(self.MODE_2CH) + ":srcffmpegworker wait() start.")
                    WavChecker.STATUSMESSAGE = "srcffmpegworker process waiting."
                    srcffmpegworker.wait()
                    self.__msgandlogging(str(self.MODE_2CH) + ":srcffmpegworker wait() done.")

                    if WavChecker.REQ_CANCEL:
                        self.__msgandlogging(level=logging.ERROR,
                                             msg=str(self.MODE_2CH) + ":" + "ffmpeg処理をキャンセルしました.")

                        self.__msgandlogging(str(self.MODE_2CH) + ":cancelled")
                        self.SIG_STOPTIMER.emit()
                        WavChecker.ISRUNNING = False
                        return

                # check normal exit?

                if srcffmpegworker:
                    # temporary wav check
                    srcwavworker.SRCPATHS = srcwavpathlist
                else:
                    # wav direct check
                    srcwavworker.SRCPATHS[0] = self.SRCPATH

                self.__msgandlogging(str(self.MODE_2CH) + ":srcwavworker start.")
                srcwavworker.start()

                # v122
                WavChecker.STATUSMESSAGE = "wavチェック中"

                orgwavworker.wait()
                srcwavworker.wait()

                self.__msgandlogging(str(self.MODE_2CH) + ":srcwavworker and orgwavworker wait() done.")

                if WavChecker.REQ_CANCEL:
                    self.__msgandlogging(str(self.MODE_2CH) + ":orgwav and srcwav cancelled")
                    self.SIG_STOPTIMER.emit()
                    WavChecker.ISRUNNING = False
                    return

                if orgwavworker.isFinished() and srcwavworker.isFinished():

                    self.__msgandlogging(str(self.MODE_2CH) + ":" + pprint.pformat(orgwavworker.checksums))
                    self.__msgandlogging(str(self.MODE_2CH) + ":" + pprint.pformat(srcwavworker.checksums))

                    if orgwavworker.checksums[self.MODE_2CH] == srcwavworker.checksums[self.MODE_2CH]:
                        self.__msgandlogging(level=logging.INFO,
                                             msg=str(self.MODE_2CH) + ":2ch(multi mono)チェックモード正常終了")
                        WavChecker.CHECKEDSTATUS = 0  # success
                        WavChecker.STATUSMESSAGE = "2ch(multi mono)チェックモード正常終了"
                    else:

                        self.work_wavbytelen = srcwavworker.work_wavbytelen
                        self.work_nchannels = srcwavworker.work_nchannels

                        self.__msgandlogging(level=logging.ERROR,
                                             msg=str(self.MODE_2CH) + ":2ch(multi mono)チェックモードエラー終了")
                        WavChecker.STATUSMESSAGE = "2ch(multi mono)チェックモードエラー終了"

                        if srcwavworker.work_samplerate == 44100 or orgwavworker.work_samplerate == 44100:
                            self.__msgandlogging(level=logging.INFO, msg="44.1khzはTC表示はできません！")
                        else:

                            if orgwavworker.checksums[WavChecker.FL] != srcwavworker.checksums[WavChecker.FL]:
                                self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_2CH) \
                                                                              + "Front Left チャンネルでエラーを検知しました！ src={0} org={1} 詳細:".format(
                                    srcwavworker.checksums[WavChecker.FL], orgwavworker.checksums[WavChecker.FL]))
                                WavChecker.STATUSMESSAGE += WavChecker.FL + " "
                                curr_retcode = self.__check_allframe2(self.MODE_2CH,
                                                                      srcwavworker.checksumframes_org[0],
                                                                      orgwavworker.checksumframes_org[0],
                                                                      srcwavworker.lastframe[0],
                                                                      orgwavworker.lastframe[0],
                                                                      srcwavworker.lastprevframe[0],
                                                                      orgwavworker.lastprevframe[0])

                                if curr_retcode > WavChecker.CHECKEDSTATUS:
                                    WavChecker.CHECKEDSTATUS = curr_retcode

                            if orgwavworker.checksums[WavChecker.FR] != srcwavworker.checksums[WavChecker.FR]:
                                self.__msgandlogging(level=logging.ERROR, msg=str(self.MODE_2CH) \
                                                                              + "Front Right チャンネルでエラーを検知しました！ src={0} org={1} 詳細:".format(
                                    srcwavworker.checksums[WavChecker.FR], orgwavworker.checksums[WavChecker.FR]))
                                WavChecker.STATUSMESSAGE += WavChecker.FR

                                curr_retcode = self.__check_allframe2(self.MODE_2CH,
                                                                      srcwavworker.checksumframes_org[1],
                                                                      orgwavworker.checksumframes_org[1],
                                                                      srcwavworker.lastframe[1],
                                                                      orgwavworker.lastframe[1],
                                                                      srcwavworker.lastprevframe[1],
                                                                      orgwavworker.lastprevframe[1])

                                if curr_retcode > WavChecker.CHECKEDSTATUS:
                                    WavChecker.CHECKEDSTATUS = curr_retcode

                else:

                    if not orgwavworker.isFinished():
                        self.__msgandlogging(level=logging.ERROR, msg=str(
                            self.MODE_2CH) + ":内部エラー:orgwavworkerスレッドが終了していません！")
                    if not srcwavworker.isFinished():
                        self.__msgandlogging(level=logging.ERROR, msg=str(
                            self.MODE_2CH) + ":内部エラー:srcwavworkerスレッドが終了していません！")

                    WavChecker.CHECKEDSTATUS = 2  # failed
                    # orgwavworker error?
                    self.__msgandlogging(level=logging.ERROR,
                                         msg=str(self.MODE_2CH) + ":" + ":内部エラー:スレッド操作エラー！")

                self.__msgandlogging(str(self.MODE_2CH) + ":終了")
                self.SIG_STOPTIMER.emit()
                WavChecker.ISRUNNING = False

            elif self.mode == self.MODE_MULTIMONO_INTERLEAVE_DANIEL:

                WavChecker.STATUSMESSAGE = "MMONO_InterLeave_Daniel mode processing started."
                self.SIG_BEGINTIMER.emit()

                WavChecker.ISRUNNING = True

                # QT or mxf
                srcffmpegworker = WavChecker(self.mainwin, self.SRC_FILE)
                srcffmpegworker.SRCPATHS = self.SRCPATHS.copy()
                srcffmpegworker.opdict = self.opdict.copy()
                srcffmpegworker.mode = self.MODE_FFMPEG_Xch_MULTIMONO

                minchnum = srcffmpegworker.opdict.get(self.OPDICT_MINWAVCHNUM)

                tempwavname = QFileInfo(self.SRCPATHS[0]).fileName() + "_SRC.wav"
                srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_interleave2ch[-1] = os.path.join(WavChecker.TEMPDIR, tempwavname)

                if srcffmpegworker.opdict.get(self.OPDICT_SOURCEWAVFORCE16BIT):
                    self.aformat = "pcm_s16le"
                    srcffmpegworker.aformat = self.aformat
                else:
                    srcffmpegworker.aformat = self.aformat

                if minchnum == 8:

                    srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_interleave2ch[8] = self.aformat
                    wk_srccmdlist = srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_interleave2ch

                if minchnum == 2:
                    srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_interleave2ch[8] = self.aformat
                    wk_srccmdlist = srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_interleave2ch

                else:
                    self.__msgandlogging(
                        "{0}:Internal error. invalid channels channelnum = {1}".format(
                            self.MODE_MULTIMONO_INTERLEAVE_DANIEL,
                            minchnum))
                    self.SIG_STOPTIMER.emit()
                    WavChecker.ISRUNNING = False

                if srcffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC):
                    # "-ss"
                    head_sssec = srcffmpegworker.opdict.get(self.OPDICT_VIDEOHEADSKIPSEC)
                    # time insert
                    wk_srccmdlist.insert(7, str(head_sssec))
                    wk_srccmdlist.insert(7, "-ss")

                # honben
                if srcffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC):
                    # "-t"
                    tail_sssec = srcffmpegworker.opdict.get(self.OPDICT_VIDEOHONBENSEC)
                    # time insert
                    wk_srccmdlist.insert(7, str(tail_sssec))
                    wk_srccmdlist.insert(7, "-t")

                # head skip

                WavChecker.PROGRESS_MAX_FFMPEG += self.opdict[self.OPDICT_SRCWAVFILESIZE]

                srcwavworker = WavChecker(self.mainwin, self.SRC_FILE)
                srcwavworker.SRCPATH = self.SRCPATHS.copy()
                srcwavworker.opdict = self.opdict.copy()
                srcwavworker.checksums[self.SRC_FILE] = srcwavworker.SRCPATH
                srcwavworker.ORGPATHS = self.ORGPATHS.copy()

                orgwavworker = WavChecker(self.mainwin, self.ORG_FILE)
                orgwavworker.SRCPATH = self.SRCPATHS.copy()
                orgwavworker.opdict = self.opdict.copy()
                orgwavworker.ORGPATHS = self.ORGPATHS.copy()
                orgwavworker.checksums[self.ORG_FILE] = orgwavworker.ORGPATHS

                srcwavworker.mode = self.MODE_WAVHASHING_SRC
                orgwavworker.mode = self.MODE_WAVHASHING_ORG

                orgwavworker.orgpathindex = 0

                # maybe org is shorter than src.

                srcffmpegworker.start()
                WavChecker.STATUSMESSAGE = "srcffmpegworker started."
                self.__msgandlogging(str(self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":srcffmpegworker start() command")

                if WavChecker.REQ_CANCEL:
                    self.__msgandlogging(level=logging.ERROR,
                                         msg=str(
                                             self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":" + "ffmpeg処理をキャンセルしました.")
                    self.SIG_STOPTIMER.emit()
                    WavChecker.ISRUNNING = False
                    return

                # start org wav hashing
                # v110
                if not self.opdict.get(WavChecker.OPDICT_CINEXCHECK):
                    # start org wav hashing
                    orgwavworker.start()

                self.__msgandlogging(str(self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":orgwavworker start()")

                self.__msgandlogging(str(self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":srcffmpegworker wait() start.")
                WavChecker.STATUSMESSAGE = "srcffmpegworker process waiting."
                srcffmpegworker.wait()
                self.__msgandlogging(str(self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":srcffmpegworker wait() done.")

                if WavChecker.REQ_CANCEL:
                    self.__msgandlogging(level=logging.ERROR,
                                         msg=str(
                                             self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":" + "ffmpeg処理をキャンセルしました.")

                    self.__msgandlogging(str(self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":cancelled")
                    self.SIG_STOPTIMER.emit()
                    WavChecker.ISRUNNING = False
                    return

                # v110 wait for CINEXCHECK wav preprocess required.
                if self.opdict.get(WavChecker.OPDICT_CINEXCHECK):
                    # v110 preprocess wav differ block

                    wk_tuple = ()
                    wk_tuple = self.preprocess_wav_forcinex(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_interleave2ch[-1],
                                                                               orgwavworker.ORGPATHS[0],
                                                                               0)
                    if wk_tuple:
                        # V122 kokokara
                        srcwavworker.cinexdiffbytes_head[0] = wk_tuple[0] # bytesarray (head diff)
                        srcwavworker.cinexdiffpos_head[0] = wk_tuple[1]   # orgindex
                        srcwavworker.cinexdiffbytes_tail[0] = wk_tuple[2] # bytesarray (tail diff)
                        # V122 kokomade
                    else:
                        WavChecker.REQ_CANCEL = True

                    if WavChecker.REQ_CANCEL:
                        self.__msgandlogging(level=logging.ERROR,
                            msg=str(self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + "src or org wavチェックをキャンセルしました.")
                        self.SIG_STOPTIMER.emit()
                        WavChecker.CHECKEDSTATUS = 1
                        WavChecker.STATUSMESSAGE = "cinexズレチェックモードがキャンセルされました"
                        WavChecker.ISRUNNING = False
                        return

                    orgwavworker.start()

                # src wavworker wav check path settings

                srcwavworker.SRCPATHS.clear()
                srcwavworker.SRCPATHS.append(srcffmpegworker.ffmpeg_8ch_multimono_cmdlist_interleave2ch[-1])

                # force end ffmpeg progress bar.
                WavChecker.PROGRESS_FFMPEG_ORG = self.opdict.get(WavChecker.OPDICT_ORGWAVFILESIZE, 0)
                WavChecker.PROGRESS_FFMPEG_SRC = self.opdict.get(WavChecker.OPDICT_SRCWAVFILESIZE, 0)

                self.__msgandlogging(str(self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":srcwavworker start.")
                WavChecker.STATUSMESSAGE = "srcwavworker start."
                srcwavworker.start()

                WavChecker.STATUSMESSAGE = "wav checking"

                orgwavworker.wait()
                srcwavworker.wait()

                self.__msgandlogging(
                    str(self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":srcwavworker and orgwavworker wait() done.")

                if WavChecker.REQ_CANCEL:
                    self.__msgandlogging(level=logging.ERROR,
                        msg=str(self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + "src or org wavチェックをキャンセルしました.")
                    self.SIG_STOPTIMER.emit()
                    WavChecker.ISRUNNING = False
                    return

                if orgwavworker.isFinished() and srcwavworker.isFinished():

                    self.__msgandlogging(
                        str(self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":" + pprint.pformat(orgwavworker.checksums))
                    self.__msgandlogging(
                        str(self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":" + pprint.pformat(srcwavworker.checksums))

                    modestr = self.MODE_INTERLEAVE

                    if orgwavworker.checksums[modestr] == srcwavworker.checksums[modestr]:
                        self.__msgandlogging(level=logging.INFO, msg=str(
                            self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + "マルチモノ＜ー＞インタリーブチェック正常終了")
                        WavChecker.CHECKEDSTATUS = 0  # success
                        WavChecker.STATUSMESSAGE = "マルチモノ＜ー＞インタリーブチェック 正常終了"
                    else:
                        self.__msgandlogging(level=logging.ERROR, msg=str(
                            self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + "マルチモノ＜ー＞インタリーブチェックエラー終了")
                        WavChecker.STATUSMESSAGE = "マルチモノ＜ー＞インタリーブチェック エラー終了"

                        self.work_wavbytelen = srcwavworker.work_wavbytelen
                        self.work_nchannels = srcwavworker.work_nchannels

                        # check all frame
                        if srcwavworker.work_samplerate == 44100 or orgwavworker.work_samplerate == 44100:
                            self.__msgandlogging(level=logging.ERROR, msg="44.1khzはTC表示はできません！")
                            WavChecker.CHECKEDSTATUS = 1  # warning
                        else:

                            self.__msgandlogging(level=logging.ERROR, msg=modestr + \
                                                                          "差異を検出しました！ src={0} org={1} 詳細:".format(
                                                                              srcwavworker.checksums[
                                                                                  WavChecker.MODE_INTERLEAVE],
                                                                              orgwavworker.checksums[
                                                                                  WavChecker.MODE_INTERLEAVE]))
                            if self.opdict.get(WavChecker.OPDICT_CINEXCHECK):

                                # V122 kokokara
                                # cinex diff check data copy to master thread.
                                self.cinexdiff_frameindex[0] = srcwavworker.cinexdiff_frameindex[0]
                                self.cinexdiffbytes_head[0] = srcwavworker.cinexdiffbytes_head[0]
                                # V122 kokomade

                            WavChecker.CHECKEDSTATUS = self.__check_allframe2(modestr,
                                                                  srcwavworker.checksumframes_org[0],
                                                                  orgwavworker.checksumframes_org[0],
                                                                  srcwavworker.lastframe[0],
                                                                  orgwavworker.lastframe[0],
                                                                  srcwavworker.lastprevframe[0],
                                                                  orgwavworker.lastprevframe[0])

                else:

                    if not orgwavworker.isFinished():
                        self.__msgandlogging(level=logging.ERROR, msg=str(
                            self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":内部エラー:orgwavworkerスレッドが終了していません！")
                    if not srcwavworker.isFinished():
                        self.__msgandlogging(level=logging.ERROR, msg=str(
                            self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":内部エラー:srcwavworkerスレッドが終了していません！")

                    WavChecker.CHECKEDSTATUS = 2  # failed
                    # orgwavworker error?
                    self.__msgandlogging(level=logging.ERROR, msg=str(
                        self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":" + ":内部エラー:スレッド操作エラー！")

                self.__msgandlogging(str(self.MODE_MULTIMONO_INTERLEAVE_DANIEL) + ":終了")
                self.SIG_STOPTIMER.emit()
                WavChecker.ISRUNNING = False

            # V130 kokokara
            elif self.mode == self.MODE_MUON_CHECK:

                WavChecker.STATUSMESSAGE = "MUON check mode processing started."
                self.SIG_BEGINTIMER.emit()
                WavChecker.ISRUNNING = True

                srcwavworker = WavChecker(self.mainwin, self.SRC_FILE)
                srcwavworker.SRCPATH = self.SRCPATHS.copy()
                srcwavworker.opdict = self.opdict.copy()
                srcwavworker.checksums[self.SRC_FILE] = srcwavworker.SRCPATH

                srcwavworker.mode = self.MODE_WAVHASHING_SRC_MUON

                # no progress ffmpeg
                WavChecker.PROGRESS_MAX_FFMPEG = 1
                WavChecker.PROGRESS_FFMPEG_SRC = 1
                WavChecker.PROGRESS_FFMPEG_ORG = 0

                self.__msgandlogging(str(self.MODE_MUON_CHECK) + ":srcwavworker start.")
                WavChecker.STATUSMESSAGE = "srcwavworker start."
                srcwavworker.start()

                WavChecker.STATUSMESSAGE = "wav checking"

                srcwavworker.wait()
                self.__msgandlogging(str(self.MODE_MUON_CHECK) + ":srcwavworker wait() done.")

                if WavChecker.REQ_CANCEL:
                    self.__msgandlogging(level=logging.ERROR,
                        msg=str(self.MODE_INTERLEAVE) + "src無音チェックをキャンセルしました.")
                    self.SIG_STOPTIMER.emit()
                    WavChecker.ISRUNNING = False
                    return

                if srcwavworker.isFinished():

                    self.__msgandlogging(str(self.MODE_MUON_CHECK) + ":" + pprint.pformat(srcwavworker.checksums[self.MODE_INTERLEAVE]))
                    # srcprintstr = pprint.pformat(srcwavworker.checksums)
                    self.__msgandlogging(str(self.MODE_MUON_CHECK) + ":" + pprint.pformat(srcwavworker.checksums[self.MODE_MUON_CHECK]))

                    # src wav MODE_INTERLEAVE = srcwav hash, src wav MODE_MUON_CHECK = 0byte xxhash wav hash
                    if srcwavworker.checksums[self.MODE_INTERLEAVE] == srcwavworker.checksums[self.MODE_MUON_CHECK]:

                        self.__msgandlogging(level=logging.INFO,
                                             msg=str(self.MODE_MUON_CHECK) + "無音チェックモード正常終了")
                        WavChecker.CHECKEDSTATUS = 0  # success
                        WavChecker.STATUSMESSAGE = "無音チェックモード正常終了"
                    else:

                        self.__msgandlogging(level=logging.ERROR,
                                             msg=str(self.MODE_MUON_CHECK) + "無音チェックモードエラー終了")
                        WavChecker.STATUSMESSAGE = "無音チェックモードエラー終了"

                        self.work_wavbytelen = srcwavworker.work_wavbytelen
                        self.work_nchannels = srcwavworker.work_nchannels

                        # V131
                        # display add virtual wav TC message display.
                        # v141
                        if self.opdict.get(WavChecker.OPDICT_STARTTCISNONE):
                            # v131a
                            self.__msgandlogging(level=logging.ERROR, msg="仮想TCとして0Hスタート 29.97fpsでTCを表示します。")

                        WavChecker.CHECKEDSTATUS = self.__check_allframe2(self.MODE_MUON_CHECK,
                                                                          srcwavworker.checksumframes_org[0],
                                                                          srcwavworker.checksumframes_muon,
                                                                          srcwavworker.lastframe[0],
                                                                          srcwavworker.checksumframes_muon[-1],
                                                                          srcwavworker.lastprevframe[0],
                                                                          srcwavworker.checksumframes_muon[-2])

                else:
                    self.__msgandlogging(level=logging.ERROR, msg=str(
                        self.MODE_MUON_CHECK) + ":内部エラー:srcwavworkerスレッドが終了していません！")
                    WavChecker.CHECKEDSTATUS = 2  # failed
                    # orgwavworker error?
                    self.__msgandlogging(level=logging.ERROR,
                                         msg=str(self.MODE_MUON_CHECK) + ":" + ":内部エラー:スレッド操作エラー！")

                self.__msgandlogging(str(self.MODE_INTERLEAVE) + ":終了")
                self.SIG_STOPTIMER.emit()
                WavChecker.ISRUNNING = False

            elif self.mode == self.MODE_WAVHASHING_SRC or self.mode == self.MODE_WAVHASHING_ORG:

                if self.name == self.SRC_FILE:
                    self.proc_wavhash4(self.SRCPATHS)
                elif self.name == self.ORG_FILE:
                    self.proc_wavhash4(self.ORGPATHS)
                else:
                    self.__msgandlogging(level=logging.ERROR, msg=str(self.mode) + ":" + "Internal error:")
            # V130
            elif self.mode == self.MODE_WAVHASHING_SRC_MUON:
                # org is not exist. orgwav max set to 100 current progress set to 100(Max)
                WavChecker.PROGRESS_MAX_ORGWAV = 100
                WavChecker.PROGRESS_ORGWAV = 100

                self.proc_wavhash4(self.SRCPATHS)
                self.proc_wavhash_muon(self.checksumframes_org[0],self.SRCPATHS)

            elif self.mode == self.MODE_FFMPEG_INTERLEAVE:
                # v141
                if self.name == self.SRC_FILE:
                    self.ffmpeg_div_command(self.SRCPATHS[0], self.mode)
                else:
                    self.ffmpeg_div_command(self.ORGPATHS[0], self.mode)

            elif self.mode == self.MODE_FFMPEG_51ch:
                if self.name == self.SRC_FILE:
                    self.ffmpeg_div_command(self.SRCPATHS[0], self.mode)
                else:
                    self.ffmpeg_div_command(self.ORGPATHS[0], self.mode)

            elif self.mode == self.MODE_FFMPEG_2ch:
                if self.name == self.SRC_FILE:
                    self.ffmpeg_div_command(self.SRCPATHS[0], self.mode)
                else:
                    self.ffmpeg_div_command(self.ORGPATHS[0], self.mode)

            elif self.mode == self.MODE_FFMPEG_8ch_MULTIMONO:
                self.ffmpeg_div_command(self.SRCPATHS[0], self.mode)

            elif self.mode == self.MODE_FFMPEG_Xch_MULTIMONO:
                self.ffmpeg_div_command(self.SRCPATHS[0], self.mode)

            else:
                self.__msgandlogging(
                    level=logging.ERROR, msg=self.name + " + Internal error:mode not implemented??:")
        except:

            etype,value,tbobj = sys.exc_info()
            self.__msgandlogging(level=logging.ERROR, msg="Python Internal Error:" + pprint.pformat(traceback.format_exception(etype,value,tbobj)))
            self.SIG_STOPTIMER.emit()
            WavChecker.CHECKEDSTATUS = 2  # failed
            WavChecker.ISRUNNING = False
            WavChecker.STATUSMESSAGE = "Python内部エラーで異常終了しました！サワツを呼べ！"

    def preprocess_wav_forcinex(self, srcwavpath, orgwavpath, channelindex):  # V110

        self.__msgandlogging(":preprocess_wav_forcinex start()")

        try:
            # v140
            srcwf = wave_bwf_rf64.open(srcwavpath, mode='rb')
        except Exception as e:
            self.__msgandlogging(level=logging.ERROR, msg=srcwavpath + ":srcwav open error, detail:" + str(e))
            WavChecker.REQ_CANCEL = True
            return None

        try:
            # v140
            orgwf = wave_bwf_rf64.open(orgwavpath, mode='rb')
        except Exception as e:
            self.__msgandlogging(level=logging.ERROR, msg=orgwavpath + ":orgwav open error, detail:" + str(e))
            WavChecker.REQ_CANCEL = True
            return None

        # v122
        diff_bytesarray_head = bytearray() # src head data
        diff_bytesarray_tail = bytearray() # org last data

        firstdiffer = True
        srcwksecbytes = None
        orgwksecbytes = None

        srcwksec_xxhash64 = xxhash.xxh3_64()
        srcwksec_xxhash64.reset()
        srcwksec_digest = None

        orgwksec_xxhash64 = xxhash.xxh3_64()
        orgwksec_xxhash64.reset()
        orgwksec_digest = None

        orgindex = 0
        srcindex = 0

        start_time = datetime.datetime.now()

        # v111 zakkuri check cinex insert zure
        # If you use 1000hz for checking all the way to the end, you may be able to judge it,
        # but I think it's okay:)
        srcwf.setpos(int(srcwf.getnframes() / 2))
        orgwf.setpos(int(orgwf.getnframes() / 2))
        startpos = srcwf.tell()

        srcwksecbytes = srcwf.readframes(srcwf.getframerate() * 10)
        orgwksecbytes = orgwf.readframes(orgwf.getframerate() * 10)
        endpos = srcwf.tell()

        srcwksec_xxhash64.update(srcwksecbytes)
        orgwksec_xxhash64.update(orgwksecbytes)

        srcwksec_digest = srcwksec_xxhash64.hexdigest()
        orgwksec_digest = orgwksec_xxhash64.hexdigest()

        if srcwksec_digest == orgwksec_digest:
            self.__msgandlogging(level=logging.ERROR,
                                 msg="入力されたSourceはcinexでインサートされていない可能性が高いため、処理をキャンセルしました。")
            self.__msgandlogging(level=logging.ERROR,
                                 msg="チェックしたサンプル範囲： {0} <-> {1}".format(startpos,endpos))
            self.__msgandlogging(level=logging.ERROR,
                                 msg="入力されたSourceがcinexインサート済みかどうか、確認してください。")
            return None

        srcwf.rewind()
        orgwf.rewind()
        srcwksec_xxhash64.reset()
        orgwksec_xxhash64.reset()
        # V111 kokomade

        current_time = datetime.datetime.now()
        elapsed_time = current_time - start_time
        self.__msgandlogging("preprocess center check time = {0}".format(elapsed_time))

        # V111
        oneblock = srcwf.getframerate() * 3 # zakkuri 1MiB kurai = 48000(khz) * 24bit(3byte) * 2(LR) = 281.5*3 = 900KiB
        self.__msgandlogging("preprocess large block chcecking started length = {0}".format(oneblock))
        while True:

            if WavChecker.REQ_CANCEL:
                return

            src1sample = srcwf.readframes(oneblock)
            srcindex += int(len(src1sample) / (srcwf.getnchannels() * srcwf.getsampwidth()))

            WavChecker.STATUSMESSAGE = "cinex ズレ検出を実行中 {0}sample/{1}sample ".format(srcindex,srcwf.getnframes())

            if firstdiffer:
                org1sample = orgwf.readframes(oneblock)
                # orgindex += oneblock
                orgindex += int(len(org1sample) / (orgwf.getnchannels() * orgwf.getsampwidth()))

            if src1sample == org1sample and firstdiffer:
                if not src1sample and not org1sample:
                    self.__msgandlogging(level=logging.ERROR,
                                         msg="入力されたSourceとOriginalの音は同一のデータです。Sourceがcinexで処理されたデータかどうか確認してください。")
                    return
                continue

            else:  # diff detected

                if firstdiffer:
                    # SAWA differ length is 5sec (=min wav length is 10sec upper ...)
                    if oneblock != 1:
                        srcwf.setpos(srcwf.tell() - oneblock) # 1block rewind
                        orgwf.setpos(orgwf.tell() - oneblock) # 1block rewind
                        srcindex -= oneblock
                        orgindex -= oneblock
                        oneblock = 1
                        self.__msgandlogging("preprocess 1sample checking started..")
                        continue

                    orgwksecbytes = org1sample + orgwf.readframes(orgwf.getframerate() * 10 - 1)
                    firstdiffer = False
                    orgwksec_xxhash64.update(orgwksecbytes)
                    orgwksec_digest = orgwksec_xxhash64.hexdigest()
                    self.__msgandlogging("orgwksec_digest = {0} orgpos = {1}".format(orgwksec_digest, orgindex))

                else:
                    curpos = srcwf.tell()
                    # differ length is 10sec (for WOWOW onair)
                    srcwksecbytes = src1sample + srcwf.readframes(srcwf.getframerate() * 10 - 1)
                    srcwf.setpos(curpos)

                    srcwksec_xxhash64.update(srcwksecbytes)
                    srcwksec_digest = srcwksec_xxhash64.hexdigest()

                    if srcwksec_digest == orgwksec_digest:

                        self.__msgandlogging("src1sec and org1sec matched! srcsamplepos = {0} orgsamplepos = {1} diff_samplenum = {2}".format(
                            srcindex,orgindex,srcindex - orgindex))
                        break
                    else:
                        srcwksec_xxhash64.reset()

                diff_bytesarray_head.extend(src1sample)


        # v122 org tail sample save.
        # org last sample located
        diffsamplenum = int(len(diff_bytesarray_head) / (orgwf.getnchannels() * orgwf.getsampwidth()))
        orgwf.setpos(orgwf.getnframes() - diffsamplenum)
        diff_bytesarray_tail = orgwf.readframes(diffsamplenum)

        current_time = datetime.datetime.now()
        elapsed_time = current_time - start_time

        self.__msgandlogging("preprocess total time = {0}".format(elapsed_time))

        return (diff_bytesarray_head,orgindex,diff_bytesarray_tail)

    def proc_wavhash4(self, paths):

        self.__msgandlogging(":proc_wavhash4 start()")

        i = 0  # channel index

        for path in paths:

            progress = 0  # progress(byte)
            j = 0  # frame index

            try:
                # v140
                wf = wave_bwf_rf64.open(path)
            except Exception as e:
                # it's almost non-standard wav reading...
                self.__msgandlogging(level=logging.ERROR, msg=path + ":wav open error, detail:" + str(e))

                self.checksums.clear()
                return (self.checksums)

            self.__msgandlogging(path + ":" + pprint.pformat(wf.getparams()))

            progress_max_total = wf.getnframes() * wf.getsampwidth() * wf.getnchannels()

            self.work_wavbytelen = wf.getsampwidth()
            self.work_nchannels = wf.getnchannels()
            self.work_samplerate = wf.getframerate()

            self.__msgandlogging("wf.chunksize(header data LL)={0}byte　progress_max_total={1}byte".format(
                wf.getchunksize(), progress_max_total))

            ma_fps = float(self.opdict[self.OPDICT_FPS])
            duration = self.opdict[self.OPDICT_MAXDURATION]
            samplerate = wf.getframerate()

            if samplerate == 44100:
                ma_fps = 30  # force 30 = 44100/30 = 1470(sample)

            elif self.opdict[self.OPDICT_FPS] == "23.98" or self.opdict[self.OPDICT_FPS] == "29.97":

                # syakuchou
                if self.opdict[self.OPDICT_FPS] == "23.98":
                    ma_fps = 24  # syakuchou
                else:
                    # 29.97 only
                    ma_fps = 30  # syakuchou
            else:
                pass

            oneframe_sz = int(samplerate / ma_fps)

            if samplerate == 44100:
                self.__msgandlogging("1frame_sz = {0} as {1}fps(44100hz fix no tc mode)".format(oneframe_sz, ma_fps))

            elif self.opdict[self.OPDICT_FPS] == "23.98":

                self.__msgandlogging("1frame_sz = {0} as {1}fps".format(oneframe_sz + int(oneframe_sz / 1000),
                                                                        self.opdict[self.OPDICT_FPS]))
            elif self.opdict[self.OPDICT_FPS] == "29.97":

                # protools sample cycle list
                # 48khz               96khz
                # 1frame = 2(sample), 3(sample)
                # 2frame = 1        , 3
                # 3frame = 2        , 4
                # 4frame = 1        , 3
                # 5frame = 2        , 3

                if samplerate == 48000:
                    self.__msgandlogging(
                        "1frame_sz protools sample pattern = {0}/{1}/{0}/{1}/{0} as {2}fps".format(oneframe_sz + 2,
                                                                                                   oneframe_sz + 1,
                                                                                                   self.opdict[
                                                                                                       self.OPDICT_FPS]))
                elif samplerate == 96000:
                    self.__msgandlogging(
                        "1frame_sz protools sample pattern = {0}/{0}/{1}/{0}/{0} as {2}fps".format(oneframe_sz + 3,
                                                                                                   oneframe_sz + 4,
                                                                                                   self.opdict[
                                                                                                       self.OPDICT_FPS]))
                else:
                    pass

            else:
                # 24,30,high framerate etc...???
                self.__msgandlogging("1frame_sz = {0} as {1}fps".format(oneframe_sz, self.opdict[self.OPDICT_FPS]))

            time_start = time.perf_counter()

            xxhash64_total = xxhash.xxh3_64()
            xxhash64_total.reset()

            xxhash64_1frame = xxhash.xxh3_64()
            xxhash64_1frame.reset()

            if self.name == self.SRC_FILE:
                WavChecker.PROGRESS_MAX_SRCWAV = progress_max_total * len(paths)
            else:  # ORG_FILE
                WavChecker.PROGRESS_MAX_ORGWAV = progress_max_total * len(paths)

            progress_max = progress_max_total

            progress_10per = ((progress_max / 100) * 10)
            progress_10_str = 10
            progress_per = progress_10per

            oneframe_sz_byte = oneframe_sz * wf.getsampwidth() * wf.getnchannels()

            oneframe_varsz = 0  # for 23.98 29.97 pattern
            fiveframe_count = 0  # for 29.97 pattern

            if self.opdict[self.OPDICT_FPS] == "23.98":
                # 23.98s is oneframe_sz + 1000/1 sample
                oneframe_varsz = int(oneframe_sz / 1000)  # 48000 -> 2(2002), 96000 -> 4(4004)

            elif self.opdict[self.OPDICT_FPS] == "29.97":

                # 29.97
                if samplerate == 48000:
                    oneframe_varsz = 2  # 48khz first frame 21212 in first 2
                elif samplerate == 96000:
                    oneframe_varsz = 3  # 96khz first frame 33433 in first 3
                else:
                    oneframe_varsz = 0  # undefined.
            else:
                # no needs adjust
                pass

            # generate empty list
            self.checksumframes_org[i] = []

            oneblock = None
            cinexdiffbytes_wk = copy.deepcopy(self.cinexdiffbytes_head[i])
            prev_pos = 0
            while True:

                # v110
                if cinexdiffbytes_wk:
                    # v122 for cinex bug head skip src diff wav.
                    diff_frames = int(len(cinexdiffbytes_wk) / (wf.getsampwidth() * wf.getnchannels()))
                    # src skip
                    # cinex diff yomisute
                    wf.readframes(diff_frames)
                    # mark yomisute ato ichi
                    prev_pos = wf.tell()
                    oneblock = wf.readframes(oneframe_sz + oneframe_varsz)
                    # print("src skip frames = {0}".format(prev_pos))
                    cinexdiffbytes_wk = None
                else:
                    prev_pos = wf.tell()
                    oneblock = wf.readframes(oneframe_sz + oneframe_varsz)

                progress += len(oneblock)

                if self.opdict[self.OPDICT_FPS] == "29.97":
                    # 29.97 sample pattern for Protools algorithm
                    # protools sample cycle list
                    # 48khz               96khz
                    # 1frame = 2(sample), 3(sample)
                    # 2frame = 1        , 3
                    # 3frame = 2        , 4
                    # 4frame = 1        , 3
                    # 5frame = 2        , 3

                    if samplerate == 48000:
                        if fiveframe_count % 2 == 0:
                            oneframe_varsz = 1  # current 1602,next 1601
                        else:
                            oneframe_varsz = 2  # current 1601,next 1602
                        fiveframe_count += 1
                        if fiveframe_count == 5:
                            fiveframe_count = 0
                            oneframe_varsz = 2  # current 1602,next 1602 (1loop)

                    # 96khz
                    elif samplerate == 96000:
                        if fiveframe_count == 1:
                            oneframe_varsz = 4  # current 3203 next 3204
                        else:
                            oneframe_varsz = 3  # current 3204 or 3203 next 3203
                        fiveframe_count += 1
                        if fiveframe_count == 5:
                            fiveframe_count = 0
                            oneframe_varsz = 3  # current 3203 next 3203 (1loop)
                    else:
                        # undefined.
                        pass

                if self.name == self.SRC_FILE:
                    WavChecker.PROGRESS_SRCWAV += len(oneblock)
                else:  # ORG_FILE
                    WavChecker.PROGRESS_ORGWAV += len(oneblock)

                # Get a progress log in 10% increments.
                if progress > progress_per:
                    self.__msgandlogging(level=logging.INFO, msg=":{0}%".format(str(progress_10_str)))
                    progress_per += progress_10per
                    progress_10_str += 10

                # no read data
                if not oneblock or WavChecker.REQ_CANCEL:
                    break

                # lastframe is not satisfyed 1frame samples?
                if len(oneblock) < oneframe_sz_byte and len(oneblock) != 0:

                    # v110
                    if not self.opdict.get(WavChecker.OPDICT_CINEXCHECK):
                        self.__msgandlogging(level=logging.WARN,
                                             msg="最終フレームのサンプル数が1フレーム未満しか存在しません。最終フレームのサンプル数={0}、パス={1}".format(
                                                 str(len(oneblock) / (wf.getsampwidth() * wf.getnchannels())), path))
                    # v122 kokokara
                    else:
                        # cinex zure hosei from org ketsu data
                        oneblock += self.cinexdiffbytes_tail[i]
                        if len(oneblock) < oneframe_sz_byte:
                            self.__msgandlogging(level=logging.WARN,
                                                 msg="cinexズレ補正を実施したにもかかわらず最終フレームのサンプル数が1フレーム未満になっています。cinexの挙動変わったかもしれないよ？".format(
                                                     str(len(oneblock) / (wf.getsampwidth() * wf.getnchannels())),
                                                     path))
                    # v122 kokomade


                # save lastframe and lastprevframe SRC or ORG
                self.lastprevframe[i] = self.lastframe[i]
                self.lastframe[i] = oneblock

                # xxhash64 total digest update
                xxhash64_total.update(oneblock)

                # xxhash64_1frame digest save
                xxhash64_1frame.update(oneblock)
                self.checksumframes_org[i].append(xxhash64_1frame.hexdigest())

                if self.opdict.get(WavChecker.OPDICT_CINEXCHECK) and self.cinexdiffpos_head[i]:
                    if self.cinexdiffpos_head[i] >= prev_pos and self.cinexdiffpos_head[i] <= wf.tell():
                        self.cinexdiffpos_head[i] = None
                        self.cinexdiff_frameindex[i] = j

                j = j + 1
                xxhash64_1frame.reset()

            if len(paths) == 1:
                # Interleave? or mono?
                self.checksums[WavChecker.MODE_INTERLEAVE] = xxhash64_total.hexdigest()

            elif len(paths) == 6:
                if i == 0:
                    self.checksums[WavChecker.FL] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_51CH] = self.checksums[WavChecker.FL]
                elif i == 1:
                    self.checksums[WavChecker.FR] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_51CH] += self.checksums[WavChecker.FR]
                elif i == 2:
                    self.checksums[WavChecker.FC] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_51CH] += self.checksums[WavChecker.FC]
                elif i == 3:
                    self.checksums[WavChecker.LFE] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_51CH] += self.checksums[WavChecker.LFE]
                elif i == 4:
                    self.checksums[WavChecker.RL] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_51CH] += self.checksums[WavChecker.RL]
                elif i == 5:
                    self.checksums[WavChecker.RR] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_51CH] += self.checksums[WavChecker.RR]
                else:
                    self.__msgandlogging(self.name + "内部矛盾エラー:5.1ch以上の処理をしようとしています")
                    self.checksums = None

            elif len(paths) == 2:

                if i == 0:
                    self.checksums[WavChecker.FL] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_2CH] = self.checksums[WavChecker.FL]
                    self.checksums[WavChecker.L] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_8CH_OA] = self.checksums[WavChecker.L]
                elif i == 1:
                    self.checksums[WavChecker.FR] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_2CH] += self.checksums[WavChecker.FR]
                    self.checksums[WavChecker.R] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_8CH_OA] += self.checksums[WavChecker.R]
                else:
                    self.__msgandlogging("内部矛盾エラー:L/Rモード選択内部矛盾、開発者に連絡してください")
                    self.checksums = None

            elif len(paths) == 8:

                if i == 0:
                    self.checksums[WavChecker.L] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_8CH_OA] = self.checksums[WavChecker.L]
                elif i == 1:
                    self.checksums[WavChecker.R] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_8CH_OA] += self.checksums[WavChecker.R]
                elif i == 2:
                    self.checksums[WavChecker.FL] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_8CH_OA] += self.checksums[WavChecker.FL]
                elif i == 3:
                    self.checksums[WavChecker.FR] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_8CH_OA] += self.checksums[WavChecker.FR]
                elif i == 4:
                    self.checksums[WavChecker.FC] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_8CH_OA] += self.checksums[WavChecker.FC]
                elif i == 5:
                    self.checksums[WavChecker.LFE] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_8CH_OA] += self.checksums[WavChecker.LFE]
                elif i == 6:
                    self.checksums[WavChecker.RL] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_8CH_OA] += self.checksums[WavChecker.RL]
                elif i == 7:
                    self.checksums[WavChecker.RR] = xxhash64_total.hexdigest()
                    self.checksums[WavChecker.MODE_8CH_OA] += self.checksums[WavChecker.RR]
                else:
                    self.__msgandlogging(self.name + "内部矛盾エラー:OA 8ch以上の処理をしようとしています")
                    self.checksums = None

            else:
                # arienai
                self.__msgandlogging("内部矛盾エラー:存在しないモード？")
                self.checksums = None

            self.__msgandlogging(str(self.checksums))

            # print(frameslist)
            self.__msgandlogging(
                "proc_wavhash4:ch={0:d} checksum calc time={1:.2f}".format(i, time.perf_counter() - time_start))
            i = i + 1

        return (self.checksums)

    # V130
    def proc_wavhash_muon(self,framehashlist,srcpaths):

        # Note:this function Prerequisites "wav" virtual 29.97fps and 48khz

        try:
            # v140
            wf = wave_bwf_rf64.open(srcpaths[0])
        except Exception as e:
            # it's almost non-standard wav reading...
            self.__msgandlogging(level=logging.ERROR, msg=srcpaths[0] + ":wav open error, detail:" + str(e))
            self.checksums.clear()
            return self.checksums

        wavbytelen = wf.getsampwidth()
        nchannels  = wf.getnchannels()
        samplerate = wf.getframerate()
        onesamplebyteslen = wavbytelen * nchannels


        if samplerate == 48000 or samplerate == 96000:
            oneframebyteslen = int((samplerate / 30) * onesamplebyteslen)
            # print("onesamplebytelen:{0}".format(oneframebyteslen))
        else:
            self.__msgandlogging(level=logging.ERROR, msg=srcpaths[0] + "samplerate can't support!!:wav open error.")
            self.checksums.clear()
            return self.checksums

        if samplerate == 48000:
            oneframe_bytearray_onelen = 2
            oneframe_bytearray_twolen = 1
        elif samplerate == 96000:
            oneframe_bytearray_onelen = 3
            oneframe_bytearray_twolen = 4
        else:
            # undefiend
            pass

        # Initialize two pattern 1frame bytearray length.
        # Ex:protools sample cycle list
        # 48khz               96khz
        # 1frame = 2(sample), 3(sample)
        # 2frame = 1        , 3
        # 3frame = 2        , 4
        # 4frame = 1        , 3
        # 5frame = 2        , 3

        # bytes
        # 48khz=2 96khz=3
        oneframe_bytearray_one = bytearray(oneframebyteslen + (onesamplebyteslen * oneframe_bytearray_onelen))
        # 48khz=1 96khz=4
        oneframe_bytearray_two = bytearray(oneframebyteslen + (onesamplebyteslen * oneframe_bytearray_twolen))

        # one xxhash initialize.
        xxhash64_muon1frame_one = xxhash.xxh3_64()
        xxhash64_muon1frame_one.reset()
        xxhash64_muon1frame_one.update(oneframe_bytearray_one)

        # for two xxhash initialize.
        xxhash64_muon1frame_two = xxhash.xxh3_64()
        xxhash64_muon1frame_two.reset()
        xxhash64_muon1frame_two.update(oneframe_bytearray_two)

        xxhash64_muonframe_total = xxhash.xxh3_64()
        xxhash64_muonframe_total.reset()

        fiveframe_count = 0  # for 29.97 pattern
        # muon 1frame bytearray work.
        muon1frame = oneframe_bytearray_one
        muon1frame_xxh = xxhash64_muon1frame_one


        for i,org1framehexdigest in enumerate(framehashlist):
            # lastframe excluded
            if i != len(framehashlist) - 1:
                # print("i={0} digest = {1}".format(i,muon1frame_xxh.hexdigest()))
                xxhash64_muonframe_total.update(muon1frame)
                self.checksumframes_muon.append(muon1frame_xxh.hexdigest())

                if samplerate == 48000:
                    if fiveframe_count % 2 == 0:
                        # 48khz next is 1
                        muon1frame = oneframe_bytearray_two
                        muon1frame_xxh = xxhash64_muon1frame_two
                    else:
                        # 48khz next is 2
                        muon1frame = oneframe_bytearray_one
                        muon1frame_xxh = xxhash64_muon1frame_one
                    fiveframe_count += 1
                    if fiveframe_count == 5:
                        # 48khz 1lap next is 2
                        fiveframe_count = 0
                        muon1frame = oneframe_bytearray_one
                        muon1frame_xxh = xxhash64_muon1frame_one
                elif samplerate == 96000:
                    if fiveframe_count == 1:
                        muon1frame = oneframe_bytearray_two
                        muon1frame_xxh = xxhash64_muon1frame_two
                    else:
                        muon1frame = oneframe_bytearray_one
                        muon1frame_xxh = xxhash64_muon1frame_one
                    fiveframe_count += 1
                    if fiveframe_count == 5:
                        fiveframe_count = 0
                        muon1frame = oneframe_bytearray_one
                        muon1frame_xxh = xxhash64_muon1frame_one
                else:
                    # undefined.
                    pass

        # lastframe wav data shorter than 1frame ?
        if len(self.lastframe[0]) != len(self.lastprevframe[0]):
            # rehash lastframe
            xxhash64_lastframe = xxhash.xxh3_64()
            xxhash64_lastframe.reset()
            lastframe_bytearray = bytearray(len(self.lastframe[0]))
            xxhash64_lastframe.update(lastframe_bytearray)
            xxhash64_muonframe_total.update(lastframe_bytearray)

            self.checksumframes_muon.append(xxhash64_lastframe.hexdigest())
        else:
            # append same muon1frame
            self.checksumframes_muon.append(muon1frame.hexdigest())
            xxhash64_muonframe_total.update(muon1frame)

        self.checksums[self.MODE_MUON_CHECK] = xxhash64_muonframe_total.hexdigest()

        return

    def __check_allframe2(self, chname, srcframelist, orgframelist, srclastframe, orglastframe,
                          srclastprevframe, orglastprevframe,chindex=0):

        retcode = 0

        tc_fpsstr = self.opdict[self.OPDICT_FPS]

        if self.opdict[self.OPDICT_FPS] == '29.97':
            if self.opdict[self.OPDICT_STARTTC][-3] == ':':
                # NDF TC treat as 30....
                # v121
                tc_fpsstr = '30'
        else:
            # other framerate
            pass

        starttc = timecode.Timecode(tc_fpsstr, self.opdict[self.OPDICT_STARTTC])


        srcduratc_frac = timecode.Timecode(tc_fpsstr)
        srcduratc_frac.set_fractional(True)
        srcduratc_frac += len(srcframelist)

        orgduratc_frac = timecode.Timecode(tc_fpsstr)
        orgduratc_frac.set_fractional(True)
        orgduratc_frac += len(orgframelist)

        self.__msgandlogging(level=logging.INFO,
                             msg="srcduration fps = {0} src duration(TC) = {1} org duration(TC) = {2} .".format(
                                 self.opdict[self.OPDICT_FPS], srcduratc_frac, orgduratc_frac))

        time_start = time.perf_counter()

        errtc_length = 0  # current error timecode object length
        errtc_sectionnum = 0  # errsection number

        i = 0

        errtc = None
        errbasetc = None
        errtclist = []  # tc tuple (TimeCode starttc, TimeCode endtc)
        basetc = starttc
        errtc_sectionnum = 0

        lasterrtc = None
        diff_length = 0

        # check length decide.
        if len(srcframelist) < len(orgframelist):
            check_length = len(srcframelist)
            diff_length = len(orgframelist) - len(srcframelist)
        else:
            check_length = len(orgframelist)
            diff_length = len(srcframelist) - len(orgframelist)

        self.__msgandlogging("checksum matching started. channel = {0} srcframenum = {1} orgframenum = {2}.".format(
            chname, len(srcframelist), len(orgframelist)))

        self.__msgandlogging("matching range: starttc = {0} endtc = {1}.".format(
            starttc, starttc + check_length))

        while i < check_length:
            if srcframelist[i] != orgframelist[i]:

                if errtc:
                    errtc += 1
                else:

                    if self.opdict[self.OPDICT_FPS] == '29.97':

                        # is non drop ?
                        if self.opdict[self.OPDICT_STARTTC][-3] == ':':
                            # nondrop(NDF) TC same as 30....
                            errbasetc = timecode.Timecode('30', start_timecode=basetc)
                            # errtc = timecode.Timecode('30', start_timecode=basetc)
                            errtc = timecode.Timecode('30', start_timecode=basetc + 1)
                        else:
                            # drop
                            errbasetc = timecode.Timecode(framerate=self.opdict[self.OPDICT_FPS], start_timecode=basetc)
                            errtc = timecode.Timecode(framerate=self.opdict[self.OPDICT_FPS], start_timecode=basetc + 1)

                    else:
                        # other frame rate
                        errbasetc = timecode.Timecode(framerate=self.opdict[self.OPDICT_FPS], start_timecode=basetc)
                        errtc = timecode.Timecode(framerate=self.opdict[self.OPDICT_FPS], start_timecode=basetc + 1)

            else:
                # frame matched
                if errtc:
                    errtctuple = (errbasetc, errtc)
                    errtclist.append(errtctuple)
                    errbasetc = None
                    errtc = None

            i += 1
            basetc += 1

        # last frame process
        if errtc:
            errtc -= 1
            errtctuple = (errbasetc, errtc + 1)
            errtclist.append(errtctuple)
            errbasetc = None
            errtc = None

        # V110 cinex special
        if self.opdict.get(WavChecker.OPDICT_CINEXCHECK):
            if self.cinexdiff_frameindex[chindex] is not None:
                # start differ tc object add.
                wk_tc = starttc + self.cinexdiff_frameindex[chindex]
                self.__msgandlogging(level=logging.ERROR,
                                     msg="CineXインサートバグによる先頭ズレを検出しました。srcのズレを補正して処理を続行します。ズレサンプル数={0}".format(
                                         int(len(self.cinexdiffbytes_head[chindex]) / (self.work_wavbytelen * self.work_nchannels))))
                retcode = 1
                # v122 return sicha dame!
                # return(retcode)

        if len(errtclist) > 0:
            self.__msgandlogging(level=logging.ERROR,
                                 msg="1フレ単位の音チェックで違いを検出しました")
            retcode = 2

        for stc, etc in errtclist:
            self.__msgandlogging(level=logging.ERROR,
                                 msg="エラーセクション{0}: 検出開始TC= {1} 検出終了TC = {2}".format( \
                                     errtc_sectionnum, stc, etc))
            lasterrtc = etc
            errtc_sectionnum += 1
        # V122 kokokara
        if errtc_sectionnum > 0:
            self.__msgandlogging(level=logging.ERROR,
                                 msg="\n")
        # V122 kokomade

        # last frame sample check
        # total frame number is same?
        if diff_length == 0:
            # last frame hash value differed ?
            if srcframelist[-1] != orgframelist[-1]:
                # v142 kokokara
                diffretcode = self.__check_1frame_1samplediff(srclastframe,
                                                              orglastframe,
                                                              lasterrtc)
                if retcode < diffretcode:
                    retcode = diffretcode
                # v142 kokomade
        else:

            difftc = 0

            if self.opdict[self.OPDICT_FPS] == '29.97' and self.opdict[self.OPDICT_STARTTC][-3] == ':':
                difftc = timecode.Timecode('30')
            else:
                # other framerate
                difftc = timecode.Timecode(self.opdict[self.OPDICT_FPS])

            difftc += diff_length
            self.__msgandlogging(level=logging.ERROR,
                                 msg="srcとorgの尺に {0} の差があります！ ={0}".format( \
                                     difftc))

            errtuple = (difftc, difftc)
            errtclist.append(errtuple)

            if diff_length == 1:
                # last frame prev hash valued differed sample showing...
                # for 1frame differd,but prev frame sample diff needed...

                # v122 kokokara
                diffretcode = self.__check_1frame_1samplediff(srclastprevframe, orglastprevframe, lasterrtc)
                if retcode < diffretcode:
                    retcode = diffretcode
                # v122 kokomade

            else:
                retcode = 2

        self.__msgandlogging(
            "checksum matching ended. chname={0} time={1:.2f}".format(chname, time.perf_counter() - time_start))

        # V131
        # V131 MUON check retcode is 0(OK) or 2(ERROR)
        if retcode == 1 and chname == self.MODE_MUON_CHECK:
            # over ride retcode to 2(ERROR)
            retcode = 2

        # retcode reference:
        # (n)frame differ is error = 2(error), last frame 5sample diff = 1(warn),no differ = 0(no error)
        return (retcode)

    def __check_1frame_1samplediff(self, srcframe, orgframe, lasterrtc):

        retcode = 0

        checklength = 0
        difflength = 0

        if len(srcframe) < len(orgframe):
            checklength = len(srcframe)
            difflength = len(orgframe) - len(srcframe)
        else:
            checklength = len(orgframe)
            difflength = len(srcframe) - len(orgframe)

        onesamplelen = self.work_wavbytelen * self.work_nchannels
        # ex: 24bit(3byte) * interleave_stere 2 = 6byte
        # sample unit convert
        difflength = difflength / onesamplelen

        i = 0
        sampleindex = 1  # position offset for protools user.

        errindex = None
        errbaseindex = None
        errsamplelist = []  # sample section tuple (samplestartindex, sampleendindex)

        while i < checklength:

            srcsample = srcframe[i:i + onesamplelen]
            orgsample = orgframe[i:i + onesamplelen]

            if srcsample != orgsample:

                if errindex:
                    errindex += 1
                else:
                    errindex = sampleindex
                    errbaseindex = sampleindex

            else:
                if errindex:
                    errtuple = (errbaseindex, errindex)
                    errsamplelist.append(errtuple)
                    errbaseindex = None
                    errindex = None

            i += onesamplelen
            sampleindex += 1

        # last frame
        if errindex:
            errtuple = (errbaseindex, errindex)
            errsamplelist.append(errtuple)
            errbaseindex = None
            errindex = None

        errsamplesection = 0

        self.__msgandlogging(level=logging.ERROR,
                             msg="エラー：ケツ1フレ内で相違があります!! TC = {0} .\n".format( \
                                 lasterrtc - 1))

        if difflength != 0:

            self.__msgandlogging(level=logging.ERROR,
                                 msg="srcとorgのケツ1フレのサンプル数比較: ソースサンプル数 = {0} オリジナルサンプル数 = {1}".format( \
                                     int((len(srcframe) / onesamplelen)),
                                     int((len(orgframe) / onesamplelen))))

            if difflength < 6:
                retcode = 1  # warn
            else:
                retcode = 2  # error

        if len(errsamplelist) == 0:
            self.__msgandlogging(level=logging.INFO,
                                 msg="sample [same] section = 0 rangeindex: 1-{0}sample .".format( \
                                     sampleindex))

        minsindex = 0

        for sindex, eindex in errsamplelist:

            if sindex == eindex:
                self.__msgandlogging(level=logging.ERROR,
                                     msg="エラーセクション {0} 位置:{1}サンプル目 .".format( \
                                         errsamplesection, sindex))
            else:
                self.__msgandlogging(level=logging.ERROR,
                                     msg="エラーセクション {0} エラー範囲: {1} - {2}サンプル間 相違サンプル数 = {3}サンプル .".format( \
                                         errsamplesection, sindex, eindex, eindex - sindex))

            errsamplesection += 1

        if errsamplesection > 1:
            retcode = 2
        elif errsamplesection == 1:
            retcode = 1
        else:
            pass

        return (retcode)

    def __msgandlogging(self, msg="", level=logging.DEBUG, display=True):

        if level == logging.ERROR:
            if display:
                self.__msglockandwrite(msg + "\n", toerrbuf=True)

        callerframe = inspect.stack()[1]  # 呼び出し元関数名取得
        newmsg = self.name + ":" + callerframe.function + ":" + str(callerframe.lineno) + ":" + msg
        if display:
            self.__msglockandwrite(newmsg + "\n")

        WavChecker.LOGGER.log(level, newmsg)

    def __filedelete(self, path):
        try:
            os.remove(path)
        except OSError as err:
            self.__msgandlogging(msg=err)

    def ffprobe_command(self, filepath):

        self.ffprobe_cmdlist[4] = filepath

        try:
            subproc = subprocess.Popen(self.ffprobe_cmdlist, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)
        except Exception as e:
            # print("ffprobe failed:" + str(e))
            self.__msgandlogging(level=logging.ERROR, msg=e)

        bufbytes = bytes()
        while True:
            line = subproc.stdout.read()
            bufbytes += line
            # print(line)

            if not line and subproc.poll() is not None:
                break
            else:
                pass

        subproc.wait()
        self.stdout = subproc.stdout
        self.stderr = subproc.stderr.read()

        if self.stderr is not None:
            self.__msgandlogging("stderr:" + str(self.stderr))

        jsondoc = QJsonDocument.fromJson(bufbytes)
        jsonobjdict = jsondoc.object()

        self.__msgandlogging("ffprobe:success. json is below:", display=False)
        self.__msgandlogging(pprint.pformat(jsonobjdict), display=False)

        streamslist = jsonobjdict["streams"]
        formatdict = jsonobjdict["format"]

        self.ffprobe_streamsdict = copy.deepcopy(streamslist)
        self.ffprobe_formatdict = copy.deepcopy(formatdict)

        return

    def ffmpeg_div_command(self, path, modename):

        try:

            # When executing extraction with ffmpeg, the progress is output to stderr for some reason.
            # At this time, if you simply read stdout, for some reason stdout will wait forever
            # (because it won't output anything?)
            # I have no choice but to mix stderr into stdout and combine the output streams.

            if modename == self.MODE_FFMPEG_INTERLEAVE:

                subproc = subprocess.Popen(self.ffmpeg_single_interleave_cmdlist,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            elif modename == self.MODE_FFMPEG_51ch:

                # v140
                if self.name == self.SRC_FILE:
                    self.ffmpeg_51ch_multimono_cmdlist[4] = path
                    subproc = subprocess.Popen(self.ffmpeg_51ch_multimono_cmdlist,
                                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                else:
                    # ORG_FILE
                    # v141 kokokara
                    if self.opdict.get(self.OPDICT_VIDEOSRCORGSWAP):
                        subproc = subprocess.Popen(self.ffmpeg_512ch_headhonbensec_cmdlist_interleave512ch,
                                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    else:
                        self.ffmpeg_51ch_multimono_cmdlist[4] = path
                        subproc = subprocess.Popen(self.ffmpeg_51ch_multimono_cmdlist,
                                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    # v141 kokomade

            elif modename == self.MODE_FFMPEG_2ch:

                self.ffmpeg_2ch_multimono_cmdlist[4] = path
                subproc = subprocess.Popen(self.ffmpeg_2ch_multimono_cmdlist,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            elif modename == self.MODE_FFMPEG_8ch_MULTIMONO:

                if len(self.ORGPATHS) == 2:
                    self.ffmpeg_8ch_multimono_cmdlist_2ch[4] = path
                    subproc = subprocess.Popen(self.ffmpeg_8ch_multimono_cmdlist_2ch,
                                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                else:
                    self.ffmpeg_8ch_multimono_cmdlist_8ch[4] = path
                    subproc = subprocess.Popen(self.ffmpeg_8ch_multimono_cmdlist_8ch,
                                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            elif modename == self.MODE_FFMPEG_Xch_MULTIMONO:

                if self.opdict.get(self.OPDICT_MINWAVCHNUM) == 2:  # minchnum
                    self.ffmpeg_8ch_multimono_cmdlist_interleave2ch[4] = path
                    subproc = subprocess.Popen(self.ffmpeg_8ch_multimono_cmdlist_interleave2ch,
                                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

                elif self.opdict.get(self.OPDICT_MINWAVCHNUM) == 8:  # minchnum
                    self.ffmpeg_8ch_multimono_cmdlist_interleave2ch[4] = path
                    subproc = subprocess.Popen(self.ffmpeg_8ch_multimono_cmdlist_interleave2ch,
                                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            else:
                self.__msgandlogging(level=logging.ERROR, msg="Internal Error. mode doesn't exist.")
                return

            self.__msgandlogging(" ".join(subproc.args))

        except Exception as e:
            self.__msgandlogging(level=logging.ERROR, msg=" ".join(subproc.args))
            self.__msgandlogging(level=logging.ERROR, msg=e)

        while True:

            if WavChecker.REQ_CANCEL:
                subproc.kill()
                break

            stdoutstr = subproc.stdout.readline()
            strlist = stdoutstr.split()

            # stdoutexample: 'size=','2085584kB','time=02:03:35.40','bitrate=2304.0kbits/s','speed=','305x'
            # print(strlist)
            # v150 ffmpeg6.1=='kB' ffmpeg 7.0=='KiB'
            if strlist and strlist[1].endswith("KiB"):

                # '2085558kB' -> extract to 2085558(int)
                filesize_byte = int(re.sub('[^0-9]', '', strlist[1]))
                # kB -> Byte unit conversion
                filesize_byte = filesize_byte * 1024

                # want to see the decoding status of ffmpeg at 1 second....

                if self.name == self.ORG_FILE:
                    if WavChecker.PROGRESS_FFMPEG_ORG != 0 and WavChecker.PROGRESS_MAX_FFMPEG != 0:
                        WavChecker.STATUSMESSAGE = "org wavを抽出中 {0}%".format(str(int((
                                                                                                    filesize_byte /
                                                                                                    self.opdict[
                                                                                                        WavChecker.OPDICT_ORGWAVFILESIZE]) * 100)))

                        self.__msgandlogging(level=logging.INFO, msg=self.name + \
                                                                     ":{0}%".format(str(int((
                                                                                                    filesize_byte /
                                                                                                    self.opdict[
                                                                                                        WavChecker.OPDICT_ORGWAVFILESIZE]) * 100))),display=False)

                        # v113
                        WavChecker.PROGRESS_FFMPEG_ORG = filesize_byte

                else:


                    if modename == self.MODE_FFMPEG_51ch:
                        # SAWA
                        filesize_byte = filesize_byte * 6

                    elif modename == self.MODE_FFMPEG_2ch:
                        filesize_byte = filesize_byte * 2
                    elif modename == self.MODE_FFMPEG_8ch_MULTIMONO:
                        # v122 kokokara
                        if self.opdict.get(self.OPDICT_MAXWAVCHNUM) == 2:
                            # chnum = 2
                            filesize_byte = filesize_byte * 2
                        else:
                            # chnum = 8
                            filesize_byte = filesize_byte * 8
                        # v122
                    elif modename == self.MODE_FFMPEG_Xch_MULTIMONO:
                        pass
                    else:
                        pass
                    WavChecker.STATUSMESSAGE = "src wavを抽出中 {0}%".format(str(int((
                                                                                            filesize_byte /
                                                                                            self.opdict[
                                                                                                WavChecker.OPDICT_SRCWAVFILESIZE]) * 100)))

                    if WavChecker.PROGRESS_FFMPEG_SRC != 0 and WavChecker.PROGRESS_MAX_FFMPEG != 0:
                        self.__msgandlogging(level=logging.INFO, msg=self.name + \
                                                                     ":{0}%".format(str(int((
                                                                                                    filesize_byte /
                                                                                                    self.opdict[
                                                                                                        WavChecker.OPDICT_SRCWAVFILESIZE]) * 100))),display=False)



                    WavChecker.PROGRESS_FFMPEG_SRC = filesize_byte

            if subproc.poll() is not None and not stdoutstr:
                break
            else:
                pass

        self.stdout = subproc.stdout.read()

        if self.stdout is not None:
            self.__msgandlogging(modename + ":pid:" + str(subproc.pid) + ":last_stdout,stderr->:" + str(self.stdout))

        self.__msgandlogging(modename + ":pid:" + str(subproc.pid) + ":ffmpeg_div() retcode=" + str(subproc.returncode))

    def msgtrylock(self):
        return (WavChecker.WavCheckMutex.tryLock(3000))

    def msgread(self):
        if WavChecker.INFOBUF:
            return WavChecker.INFOBUF
        else:
            return None

    def msgread_error(self):
        if WavChecker.ERRBUF:
            return WavChecker.ERRBUF
        else:
            return None

    def msgclear(self):
        WavChecker.INFOBUF = ''

    def msgclear_error(self):
        WavChecker.ERRBUF = ''

    def msgunlock(self):
        WavChecker.WavCheckMutex.unlock()
        return

    def __msglockandwrite(self, msg, toerrbuf=False):
        if (WavChecker.WavCheckMutex.tryLock(3000)):
            WavChecker.INFOBUF += msg

            if toerrbuf:
                WavChecker.ERRBUF += msg

            WavChecker.WavCheckMutex.unlock()


# main method
if __name__ == '__main__':
    import sys
    from PySide2 import QtWidgets, QtCore
    from PySide2 import QtCore
    from mainwindow import MainWindow

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)

    window.show()
    sys.exit(app.exec_())

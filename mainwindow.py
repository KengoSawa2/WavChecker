# -*- coding: utf-8 -*-
import copy
import pprint
import sys
import re
import datetime

from mainwindow_ui import *

from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2.QtWidgets import QFileDialog
from PySide2.QtCore import QFileInfo
from PySide2.QtGui import QTextCursor
from PySide2.QtGui import QIntValidator
from PySide2.QtCore import QRegularExpression

from WavChecker import WavChecker

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    '''
    WAVCHECKER MainWindow
    '''

    __version__ = WavChecker.__version__

    def __init__(self, app):
        super(MainWindow, self).__init__()

        self.msgbuf = ""

        self.wavchecker = WavChecker(self, WavChecker.MASTER)
        self.wavchecker.logger_init()

        self.setupUi(self)
        self.setWindowTitle("QTWavChecker v" + self.__version__)

        self.__initEv()

        self.timerid = 0
        self.lasttimer = False
        self.dot_count = 0
        self.starttime = ""
        # save default pallete
        self.defaultpalette = self.plainTextEdit_log.palette()

        self.comboBox_source.setCurrentIndex(1)
        self.comboBox_source.setCurrentIndex(0)

        self.source_audioformatdict = {}  # ex:{'avg_frame_rate': '0/0','bit_rate': '2304000','bits_per_sample': '24'}
        self.original_audioformatdict = {}  # ex:↑

        self.sourcevideoisdrop = False
        self.isbsordel = False
        self.numkeylist = [Qt.Key_0, Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5, Qt.Key_6, Qt.Key_7, Qt.Key_8,
                           Qt.Key_9]

    def __initEv(self):

        self.setAcceptDrops(True)
        self.wavchecker.SIG_BEGINTIMER.connect(self.beginTimer)
        self.wavchecker.SIG_STOPTIMER.connect(self.stopTimer)

        self.pushButton_sourceQT.clicked.connect(self.SourceOrgWavselected)
        self.lineEdit_sourcefile.setAcceptDrops(True)
        self.comboBox_source.currentIndexChanged.connect(self._Modeindexchanged)
        self.pushButton_Start.clicked.connect(self._CheckStarted)

        self.pushButton_AllReset.clicked.connect(self._AllReset)

        # 2ch stereo(InterLeave mode)
        self.pushButton_2ch.clicked.connect(self.SourceOrgWavselected)

        # 5.1ch(Include 2ch multi mono(FL,FR))
        self.pushButton_51ch_FR.clicked.connect(self.SourceOrgWavselected)
        self.pushButton_51ch_FL.clicked.connect(self.SourceOrgWavselected)
        self.pushButton_51ch_RR.clicked.connect(self.SourceOrgWavselected)
        self.pushButton_51ch_RL.clicked.connect(self.SourceOrgWavselected)
        self.pushButton_51ch_FC.clicked.connect(self.SourceOrgWavselected)
        self.pushButton_51ch_LFE.clicked.connect(self.SourceOrgWavselected)
        self.pushButton_8ch_R.clicked.connect(self.SourceOrgWavselected)
        self.pushButton_8ch_L.clicked.connect(self.SourceOrgWavselected)

        self.wavchecker.finished.connect(self.finishThread)

        self.status_label = QtWidgets.QLabel()
        self.status_label = QtWidgets.QLabel()
        self.status_label.setAlignment(QtCore.Qt.AlignLeft)

        self.statusBar().addWidget(self.status_label)

        self.groupBox_videoinout.clicked.connect(self.__hide_videoinout)
        self.lineEdit_videoin.textChanged.connect(self.__videoinout_changed)
        self.lineEdit_videohonben.textChanged.connect(self.__videoinout_changed)

        self.__hide_videoinout(self.groupBox_videoinout.isChecked())

        self.groupBox_videoinout.setDisabled(True)

        self.iv = QIntValidator(0, 2147483647, self.lineEdit_videoin)
        self.lineEdit_videoin.setValidator(self.iv)

        self.rx = QRegExp("^(((([0-1][0-9])|(2[0-3])):[0-5][0-9]:[0-5][0-9]$))|")
        self.honbenv = QRegExpValidator(self.rx, self.lineEdit_videohonben)
        self.lineEdit_videohonben.setValidator(self.honbenv)

        self.textEdit_errlog.hide()
        self.label_errlog.hide()

        self.installEventFilter(self)
        self.lineEdit_videohonben.installEventFilter(self)

        # set default size(all object displays at 1920x1080)
        self.resize(self.minimumSize())

        return

    def _Modeindexchanged(self, index):

        if index == 0:
            # Interleave mode
            self.stackedWidget.setCurrentIndex(index)
            self.groupBox_original.setMaximumHeight(150)
            self.pushButton_sourceQT.setText("Source QT,MXF,wav")
            self.lineEdit_sourcefile.setPlaceholderText("D&D QT or MXF or wav(Interleave/Interleave or Mono/Mono)")
            self.pushButton_2ch.setText("Original QT,MXF,wav")
            self.lineEdit_2ch.setPlaceholderText("D&D QT or MXF or wav(Interleave/Interleave or Mono/Mono)")
            self.checkBox_cinex.setChecked(False)
            self.checkBox_cinex.hide()
            # V130
            self.groupBox_original.show()
            self.__show_selectstream()
            # v131b
            self.groupBox_audio.show()
            self.checkBox_force16bit.show()
            # v140
            self.checkBox_videoswapsrcorg.setChecked(False)
            self.checkBox_videoswapsrcorg.setEnabled(False)

            self.resize(self.width(),820)

        elif index == 1:
            # source interleave org mono 6ch(5.1) mode.
            self._setvisible_RLRRFLLFE(True)
            self._setvisible_LR(False)
            self.stackedWidget.setCurrentIndex(index)
            self.groupBox_original.setMaximumHeight(450)
            self.pushButton_sourceQT.setText("Source QT,MXF")
            self.lineEdit_sourcefile.setPlaceholderText("D&D QT,MXF(Interleave only)")
            self.checkBox_cinex.setChecked(False)
            self.checkBox_cinex.hide()
            # V130
            self.groupBox_original.show()
            self.__hide_selectstream()
            # v131b
            self.groupBox_audio.show()
            self.checkBox_force16bit.show()

            # v140
            self.checkBox_videoswapsrcorg.setEnabled(True)
            self.checkBox_videoswapsrcorg.setChecked(False)

            self.resize(self.width(),1000)

        elif index == 2:
            # source interleave org mono 2ch mode.
            self._setvisible_RLRRFLLFE(False)
            self._setvisible_LR(False)
            self.stackedWidget.setCurrentIndex(1)
            self.groupBox_original.setMaximumHeight(250)
            self.pushButton_sourceQT.setText("Source QT,MXF")
            self.lineEdit_sourcefile.setPlaceholderText("D&D QT,MXF(Interleave only)")
            self.checkBox_cinex.setChecked(False)
            self.checkBox_cinex.hide()
            # V130
            self.groupBox_original.show()
            self.__hide_selectstream()

            # v131b
            self.groupBox_audio.show()
            self.checkBox_force16bit.show()
            # v140
            self.checkBox_videoswapsrcorg.setEnabled(True)
            self.checkBox_videoswapsrcorg.setChecked(False)

            self.resize(self.width(),820)

        elif index == 3:

            # source multimono org mono 2ch or 8ch(2ch+5.1ch) mode
            self._setvisible_LR(True)
            self._setvisible_RLRRFLLFE(True)
            self.stackedWidget.setCurrentIndex(1)
            self.groupBox_original.setMaximumHeight(650)
            self.pushButton_sourceQT.setText("Source MXF")
            self.lineEdit_sourcefile.setPlaceholderText("D&D MXF(Multi Mono only)")
            self.checkBox_cinex.show()
            # V130
            self.groupBox_original.show()
            self.__hide_selectstream()

            # v131b
            self.groupBox_audio.show()
            self.checkBox_force16bit.show()

            # v140
            self.checkBox_videoswapsrcorg.setChecked(False)
            self.checkBox_videoswapsrcorg.setEnabled(False)

            self.resize(self.width(),1080)


        elif index == 4:

            # source multimono org Interleave mode.
            self.stackedWidget.setCurrentIndex(0)
            self.groupBox_original.setMaximumHeight(150)
            self.pushButton_sourceQT.setText("Source QT,MXF")
            self.lineEdit_sourcefile.setPlaceholderText("D&D MXF(Multi Mono only)")
            self.pushButton_2ch.setText("Original wav")
            self.lineEdit_2ch.setPlaceholderText("D&D original wav(2ch Interleave only)")
            self.checkBox_cinex.show()
            # V130
            self.__hide_selectstream()
            self.groupBox_original.show()

            # v131b
            self.groupBox_audio.show()
            self.checkBox_force16bit.show()

            # v140
            self.checkBox_videoswapsrcorg.setChecked(False)
            self.checkBox_videoswapsrcorg.setEnabled(False)

            self.resize(self.width(),820)

        # V130
        elif index == 5:

            # v141 muon check mode
            self.original_audioformatdict.clear()

            self.stackedWidget.setCurrentIndex(0)
            self.groupBox_original.hide()

            self.pushButton_sourceQT.setText("Source wav")
            self.lineEdit_sourcefile.setPlaceholderText("D&D wav")

            self.checkBox_cinex.setChecked(False)
            self.checkBox_cinex.hide()
            self.checkBox_force16bit.setChecked(False)
            self.checkBox_force16bit.hide()
            self.__hide_selectstream()

            # v140
            self.checkBox_videoswapsrcorg.setChecked(False)
            self.checkBox_videoswapsrcorg.setEnabled(False)

            self.resize(self.width(),520)

    def _setvisible_RLRRFLLFE(self, isvisible):

        # RL hide
        self.label_RLINFO.setVisible(isvisible)
        self.lineEdit_51ch_RL.setVisible(isvisible)
        self.pushButton_51ch_RL.setVisible(isvisible)

        # RR hide
        self.label_RRINFO.setVisible(isvisible)
        self.lineEdit_51ch_RR.setVisible(isvisible)
        self.pushButton_51ch_RR.setVisible(isvisible)

        # FC
        self.label_FCINFO.setVisible(isvisible)
        self.lineEdit_51ch_FC.setVisible(isvisible)
        self.pushButton_51ch_FC.setVisible(isvisible)

        # LFE
        self.label_LFEINFO.setVisible(isvisible)
        self.lineEdit_51ch_LFE.setVisible(isvisible)
        self.pushButton_51ch_LFE.setVisible(isvisible)

    def _setvisible_LR(self, isvisible):

        # L hide
        self.label_LINFO.setVisible(isvisible)
        self.lineEdit_8ch_L.setVisible(isvisible)
        self.pushButton_8ch_L.setVisible(isvisible)

        # R hide
        self.label_RINFO.setVisible(isvisible)
        self.lineEdit_8ch_R.setVisible(isvisible)
        self.pushButton_8ch_R.setVisible(isvisible)

    def dragEnterEvent(self, event):

        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):

        urls = event.mimeData().urls()

        pathlist = []  # multiple file D&D for 2ch multimono or 5.1ch multi mono mode

        # InterLeave mode with multiple files.
        if len(urls) > 1 and self.comboBox_source.currentIndex() == 0:
            return

        for url in urls:
            path = url.path()
            pathlist.append(path)

        # src drop
        if (self.lineEdit_sourcefile.rect().contains(self.lineEdit_sourcefile.mapFromGlobal(QtGui.QCursor.pos()))):

            # V130
            if (QFileInfo(path).suffix() == "wav"):
                #V130 muon check tsuika
                if self.comboBox_source.currentIndex() == 0 or self.comboBox_source.currentIndex() == 5:
                    self.lineEdit_sourcefile.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_sourcefile, self.label_sourceAudio, True)

                else:
                    QMessageBox.critical(self, None,
                                         "Sourcheへのwav入力はインタリーブ＜ー＞インタリーブモードと無音チェックのみ対応です！",
                                         QMessageBox.Ok)


            elif QFileInfo(path).suffix() == "mov" or QFileInfo(path).suffix() == "mxf":
                self.lineEdit_sourcefile.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_sourcefile, self.label_sourceVideo, True)

            else:
                # self.textEdit_errlog.append("Interleave mode allow mov and wav, other mode only mov !!.")
                QMessageBox.critical(self, None,
                                     "未サポートの拡張子です\nサポート拡張子はmov,mxf,wavです\n増やしたかったらサワツにお願いしてね！",
                                     QMessageBox.Ok)

        # org drop
        if QFileInfo(path).suffix() == "wav":

            # Interleave
            if self.comboBox_source.currentIndex() == 0 and \
                    self.lineEdit_2ch.rect().contains(self.lineEdit_2ch.mapFromGlobal(QtGui.QCursor.pos())):

                self.lineEdit_2ch.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_2ch, self.label_2chINFO)

            # 5.1ch
            elif self.comboBox_source.currentIndex() == 1:
                self._51ch_drop(pathlist)

            # 2ch multi mono
            elif self.comboBox_source.currentIndex() == 2:
                self._51ch_drop(pathlist)

            # 8ch oa mode
            elif self.comboBox_source.currentIndex() == 3:
                self._8ch_drop(pathlist)

            elif self.comboBox_source.currentIndex() == 4 and \
                    self.lineEdit_2ch.rect().contains(self.lineEdit_2ch.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_2ch.setText(path)
                self.SourceOrgWavselected(path,self.lineEdit_2ch, self.label_2chINFO)

            else:
                pass

        if QFileInfo(path).suffix() == "mov" or QFileInfo(path).suffix() == "mxf":
            if self.lineEdit_2ch.rect().contains(self.lineEdit_2ch.mapFromGlobal(QtGui.QCursor.pos())):
                if self.comboBox_source.currentIndex() == 0:
                    self.lineEdit_2ch.setText(path)
                    self.SourceOrgWavselected(path,self.lineEdit_2ch,self.label_2chINFO)

    def closeEvent(self, event):

        # ffmpegの途中経過出力用にとっといたwavを削除
        self.wavchecker.tempfile_del()

    def _51ch_drop(self, pathlist):

        # '.L' '.R' のようにProtoolsの5.1ch書き出しファイル名でまとめてD&D入力するとそれっぽく自動でアサインするよ
        # Protools慣習に従ってるだけだよ。
        if len(pathlist) == 6 or len(pathlist) == 2:
            for path in pathlist:
                if path.endswith('.R.wav'):
                    # 5.1ch Front Right
                    self.lineEdit_51ch_FR.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_51ch_FR, self.label_FRINFO)
                elif path.endswith('.L.wav'):
                    # 5.1ch Front Left
                    self.lineEdit_51ch_FL.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_51ch_FL, self.label_FLINFO)
                elif path.endswith('.Rs.wav'):
                    self.lineEdit_51ch_RR.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_51ch_RR, self.label_RRINFO)
                elif path.endswith('.Ls.wav'):
                    self.lineEdit_51ch_RL.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_51ch_RL, self.label_RLINFO)
                elif path.endswith('.C.wav'):
                    self.lineEdit_51ch_FC.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_51ch_FC, self.label_FCINFO)
                elif path.endswith('.LFE.wav'):
                    self.lineEdit_51ch_LFE.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_51ch_LFE, self.label_LFEINFO)

        else:
            path = pathlist[0]
            # 5.1ch Front Right
            if self.lineEdit_51ch_FR.rect().contains(self.lineEdit_51ch_FR.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_51ch_FR.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_51ch_FR, self.label_FRINFO)

            # 5.1ch Front Left
            elif self.lineEdit_51ch_FL.rect().contains(self.lineEdit_51ch_FL.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_51ch_FL.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_51ch_FL, self.label_FLINFO)

            # 5.1ch Rear Right
            elif self.lineEdit_51ch_RR.rect().contains(self.lineEdit_51ch_RR.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_51ch_RR.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_51ch_RR, self.label_RRINFO)

            # 5.1ch Rear Left
            elif self.lineEdit_51ch_RL.rect().contains(self.lineEdit_51ch_RL.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_51ch_RL.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_51ch_RL, self.label_RLINFO)

            # 5.1ch Front Center
            elif self.lineEdit_51ch_FC.rect().contains(self.lineEdit_51ch_FC.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_51ch_FC.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_51ch_FC, self.label_FCINFO)

            # 5.1ch LFE
            elif self.lineEdit_51ch_LFE.rect().contains(self.lineEdit_51ch_LFE.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_51ch_LFE.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_51ch_LFE, self.label_LFEINFO)

    def _8ch_drop(self, pathlist):

        # L,Rを同時に入れるなら、ファイル名でええ感じに取り込んでやろう
        if len(pathlist) == 2:  # L,R
            for path in pathlist:
                if path.endswith('.R.wav'):
                    # 8ch Right
                    self.lineEdit_8ch_R.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_8ch_R, self.label_RINFO)
                elif path.endswith('.L.wav'):
                    # 5.1ch Front Left
                    self.lineEdit_8ch_L.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_8ch_L, self.label_LINFO)

        # D&D with the Protools 5.1ch export file name like '.L' and '.R', it will be automatically assigned.
        # Just following Protools conventions.
        elif len(pathlist) == 8:
            for path in pathlist:

                if path.endswith('.R.wav'):
                    # 8ch Right
                    self.lineEdit_8ch_R.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_8ch_R, self.label_RINFO)
                elif path.endswith('.L.wav'):
                    # 5.1ch Front Left
                    self.lineEdit_8ch_L.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_8ch_L, self.label_LINFO)
                elif path.endswith('.Fr.wav'):
                    # 5.1ch Front Right
                    self.lineEdit_51ch_FR.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_51ch_FR, self.label_FRINFO)
                elif path.endswith('.Fl.wav'):
                    # 5.1ch Front Left
                    self.lineEdit_51ch_FL.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_51ch_FL, self.label_FLINFO)
                elif path.endswith('.Rs.wav'):
                    self.lineEdit_51ch_RR.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_51ch_RR, self.label_RRINFO)
                elif path.endswith('.Ls.wav'):
                    self.lineEdit_51ch_RL.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_51ch_RL, self.label_RLINFO)
                elif path.endswith('.C.wav'):
                    self.lineEdit_51ch_FC.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_51ch_FC, self.label_FCINFO)
                elif path.endswith('.LFE.wav'):
                    self.lineEdit_51ch_LFE.setText(path)
                    self.SourceOrgWavselected(path, self.lineEdit_51ch_LFE, self.label_LFEINFO)

        else:
            path = pathlist[0]
            # 8ch L
            if self.lineEdit_8ch_L.rect().contains(self.lineEdit_8ch_L.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_8ch_L.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_8ch_L, self.label_LINFO)

            # 8ch R
            if self.lineEdit_8ch_R.rect().contains(self.lineEdit_8ch_R.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_8ch_R.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_8ch_R, self.label_RINFO)

            # 5.1ch Front Right
            if self.lineEdit_51ch_FR.rect().contains(self.lineEdit_51ch_FR.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_51ch_FR.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_51ch_FR, self.label_FRINFO)

            # 5.1ch Front Left
            elif self.lineEdit_51ch_FL.rect().contains(self.lineEdit_51ch_FL.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_51ch_FL.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_51ch_FL, self.label_FLINFO)

            # 5.1ch Rear Right
            elif self.lineEdit_51ch_RR.rect().contains(self.lineEdit_51ch_RR.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_51ch_RR.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_51ch_RR, self.label_RRINFO)

            # 5.1ch Rear Left
            elif self.lineEdit_51ch_RL.rect().contains(self.lineEdit_51ch_RL.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_51ch_RL.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_51ch_RL, self.label_RLINFO)

            # 5.1ch Front Center
            elif self.lineEdit_51ch_FC.rect().contains(self.lineEdit_51ch_FC.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_51ch_FC.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_51ch_FC, self.label_FCINFO)

            # 5.1ch LFE
            elif self.lineEdit_51ch_LFE.rect().contains(self.lineEdit_51ch_LFE.mapFromGlobal(QtGui.QCursor.pos())):
                self.lineEdit_51ch_LFE.setText(path)
                self.SourceOrgWavselected(path, self.lineEdit_51ch_LFE, self.label_LFEINFO)

    def _CheckStarted(self):

        if WavChecker.ISRUNNING and WavChecker.REQ_CANCEL == False:
            WavChecker.REQ_CANCEL = True
            return

        self.wavchecker.reset()

        self.progressBar_ffmpeg.setValue(0)
        self.progressBar_orgwav.setValue(0)
        self.progressBar_srcwav.setValue(0)
        self.plainTextEdit_log.setStyleSheet("QPlainTextEdit {background-color:#FFFFFF;}")
        self.textEdit_errlog.clear()
        self.textEdit_errlog.setStyleSheet("QTextEdit {background-color: #FFFFFF;color: #000000}")
        self.label_errlog.hide()
        self.textEdit_errlog.hide()

        WavChecker.tempfile_init()

        orgpathlist = []

        # If pcm data is big endian, convert it to little endian.
        # The reason is that ffmpeg does not support bigendian WAV output using the RIFX header.
        # For Example. Baselight output QT is bigendian.
        if self.source_audioformatdict.get("codec_name").endswith("be"):
            wk_aformat = self.source_audioformatdict.get("codec_name")
            result = wk_aformat[:-2] + "le"  # pcm_s24be -> pcm_s24le
            self.wavchecker.aformat = result
        # V130 for muon check
        elif len(self.original_audioformatdict) and self.original_audioformatdict.get("codec_name").endswith("be"):
            wk_aformat = self.original_audioformatdict.get("codec_name")
            result = wk_aformat[:-2] + "le"
            self.wavchecker.aformat = result
        else:
            self.wavchecker.aformat = self.source_audioformatdict.get("codec_name")

        # Head cut function enabled?
        if self.groupBox_videoinout.isEnabled() and self.groupBox_videoinout.isChecked():

            if self.lineEdit_videoin.text():

                if self.sourceisthousand:
                    # 23.98,29.97 has extra sound, so calculate the offset number of seconds.
                    # ---head 5sec-------   --------honben------   ---tail 5sec-------
                    # <5sec> + <0.005sec> + <15sec> + <0.015sec> + <5sec> + <0.005>sec
                    # When specifying the position on the ffmpeg side, based on the above,
                    # you must add 1/1000th of a second to the head time and honben.
                    head_float = float(self.lineEdit_videoin.text())
                    head_float = head_float + head_float / 1000  # ex:120 -> 120.12, 5 -> 5.005
                    self.wavchecker.opdict[self.wavchecker.OPDICT_VIDEOHEADSKIPSEC] = str(head_float)

                else:
                    # no adjust
                    self.wavchecker.opdict[self.wavchecker.OPDICT_VIDEOHEADSKIPSEC] = self.lineEdit_videoin.text()

            if self.lineEdit_videohonben.text():

                # If hh:mm:ss format, convert to total seconds, otherwise use as is
                hmslist = self.lineEdit_videohonben.text().split(":")

                if len(hmslist) == 1:
                    # sec only input
                    honben_float = float(hmslist[0])

                elif len(hmslist) == 3:
                    # hh:mm:ss input
                    td = datetime.timedelta(hours=int(hmslist[0]), minutes=int(hmslist[1]), seconds=int(hmslist[2]))
                    honben_float = float(td.seconds)

                else:
                    QMessageBox.critical(self, None,
                                         "honbenの入力数値の形式が正しくありません！hh:mm:ssで入力してください！",
                                         QMessageBox.Ok)
                    return

                if self.sourceisthousand:
                    honben_float = honben_float + honben_float / 1000

                self.wavchecker.opdict[self.wavchecker.OPDICT_VIDEOHONBENSEC] = str(honben_float)
            # v140
            if self.checkBox_videoswapsrcorg.isChecked():
                self.wavchecker.opdict[self.wavchecker.OPDICT_VIDEOSRCORGSWAP] = True

        if self.checkBox_force16bit.isChecked():
            self.wavchecker.opdict[self.wavchecker.OPDICT_SOURCEWAVFORCE16BIT] = True
        # v113
        else:
            self.wavchecker.opdict[self.wavchecker.OPDICT_SOURCEWAVFORCE16BIT] = False

        if self.checkBox_cinex.isChecked():
            self.wavchecker.opdict[self.wavchecker.OPDICT_CINEXCHECK] = True
        # v113
        else:
            self.wavchecker.opdict[self.wavchecker.OPDICT_CINEXCHECK] = False

        # Interleave <-> Interleave
        if self.comboBox_source.currentIndex() == 0:

            if QFileInfo(self.lineEdit_sourcefile.text()).exists() \
                    and QFileInfo(self.lineEdit_2ch.text()).exists():

                # v130
                if self.comboBox_sourcechannel.isVisible() and self.comboBox_sourcechannel.count() > 1:
                    self.wavchecker.opdict[self.wavchecker.OPDICT_SELECTINDEX] = self.comboBox_sourcechannel.currentIndex()
                    # src one index select in multi index(over write predict size).
                    self.wavchecker.opdict[self.wavchecker.OPDICT_SRCWAVFILESIZE] = self.wavchecker.opdict[self.wavchecker.OPDICT_ORGWAVFILESIZE]

                self.wavchecker.mode = self.wavchecker.MODE_INTERLEAVE
                WavChecker.SRCPATHS.append(self.lineEdit_sourcefile.text())
                orgpathlist.append(self.lineEdit_2ch.text())
                WavChecker.ORGPATHS = orgpathlist.copy()
                self.wavchecker.start()
                # self.pushButton_Start.setEnabled(False)
                self.pushButton_Start.setText("「Cancel..」")
                self.pushButton_AllReset.setEnabled(False)

                # start checking?

            else:
                QMessageBox.critical(self, None,
                                     "ソースのパスまたはオリジナルのパスが間違っています！\n正しく設定してください！",
                                     QMessageBox.Ok)

        # 5.1ch
        elif self.comboBox_source.currentIndex() == 1:
            if QFileInfo(self.lineEdit_sourcefile.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_FL.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_FR.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_FC.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_LFE.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_RL.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_RR.text()).exists():

                self.wavchecker.mode = self.wavchecker.MODE_51CH
                WavChecker.SRCPATHS.append(self.lineEdit_sourcefile.text())
                self.wavchecker.aformat = self.source_audioformatdict.get("codec_name")

                orgpathlist.append(self.lineEdit_51ch_FL.text())
                orgpathlist.append(self.lineEdit_51ch_FR.text())
                orgpathlist.append(self.lineEdit_51ch_FC.text())
                orgpathlist.append(self.lineEdit_51ch_LFE.text())
                orgpathlist.append(self.lineEdit_51ch_RL.text())
                orgpathlist.append(self.lineEdit_51ch_RR.text())
                WavChecker.ORGPATHS = orgpathlist.copy()
                self.wavchecker.start()
                self.pushButton_Start.setText("「Cancel..」")
                self.pushButton_AllReset.setEnabled(False)

            else:
                QMessageBox.critical(self, None,
                                     "ソースのパスまたはオリジナルのパスが間違っています！\n正しく設定してください！",
                                     QMessageBox.Ok)

        # 2ch (multi mono)
        elif self.comboBox_source.currentIndex() == 2:
            if QFileInfo(self.lineEdit_sourcefile.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_FL.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_FR.text()).exists():

                self.wavchecker.mode = self.wavchecker.MODE_2CH
                WavChecker.SRCPATHS.append(self.lineEdit_sourcefile.text())
                self.wavchecker.aformat = self.source_audioformatdict.get("codec_name")

                orgpathlist.append(self.lineEdit_51ch_FL.text())
                orgpathlist.append(self.lineEdit_51ch_FR.text())
                WavChecker.ORGPATHS = orgpathlist.copy()
                self.wavchecker.start()
                self.pushButton_Start.setText("「Cancel..」")
                self.pushButton_AllReset.setEnabled(False)

            else:
                QMessageBox.critical(self, None,
                                     "ソースのパスまたはオリジナルのパスが間違っています！\n正しく設定してください！",
                                     QMessageBox.Ok)
        # 8ch (MXF OA mode)
        elif self.comboBox_source.currentIndex() == 3:

            # 2ch exists check
            if QFileInfo(self.lineEdit_sourcefile.text()).exists() \
                    and QFileInfo(self.lineEdit_8ch_L.text()).exists() \
                    and QFileInfo(self.lineEdit_8ch_R.text()).exists():

                self.wavchecker.mode = self.wavchecker.MODE_8CH_OA
                WavChecker.SRCPATHS.append(self.lineEdit_sourcefile.text())
                self.wavchecker.aformat = self.source_audioformatdict.get("codec_name")

                orgpathlist.append(self.lineEdit_8ch_L.text())
                orgpathlist.append(self.lineEdit_8ch_R.text())

                # +6ch exists ?
                if QFileInfo(self.lineEdit_51ch_FL.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_FR.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_FC.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_LFE.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_RL.text()).exists() \
                    and QFileInfo(self.lineEdit_51ch_RR.text()).exists():

                    # add 6ch paths
                    orgpathlist.append(self.lineEdit_51ch_FL.text())
                    orgpathlist.append(self.lineEdit_51ch_FR.text())
                    orgpathlist.append(self.lineEdit_51ch_FC.text())
                    orgpathlist.append(self.lineEdit_51ch_LFE.text())
                    orgpathlist.append(self.lineEdit_51ch_RL.text())
                    orgpathlist.append(self.lineEdit_51ch_RR.text())

                WavChecker.ORGPATHS = orgpathlist.copy()
                self.wavchecker.start()
                self.pushButton_Start.setText("「Cancel..」")
                self.pushButton_AllReset.setEnabled(False)

            else:
                QMessageBox.critical(self, None,
                                     "ソースのパスまたはオリジナルのパスが間違っています！\n正しく設定してください！",
                                     QMessageBox.Ok)

        elif self.comboBox_source.currentIndex() == 4:

            if QFileInfo(self.lineEdit_sourcefile.text()).exists() \
                    and QFileInfo(self.lineEdit_2ch.text()).exists():
                self.wavchecker.mode = self.wavchecker.MODE_MULTIMONO_INTERLEAVE_DANIEL
                WavChecker.SRCPATHS.append(self.lineEdit_sourcefile.text())
                orgpathlist.append(self.lineEdit_2ch.text())
                WavChecker.ORGPATHS = orgpathlist.copy()
                self.wavchecker.start()
                # self.pushButton_Start.setEnabled(False)
                self.pushButton_Start.setText("「Cancel..」")
                self.pushButton_AllReset.setEnabled(False)

                # start checking?

            else:
                QMessageBox.critical(self, None,
                                     "ソースのパスまたはオリジナルのパスが間違っています！\n正しく設定してください！",
                                     QMessageBox.Ok)

        # V130
        elif self.comboBox_source.currentIndex() == 5:

            if QFileInfo(self.lineEdit_sourcefile.text()).exists():
                self.wavchecker.mode = self.wavchecker.MODE_MUON_CHECK
                WavChecker.SRCPATHS.append(self.lineEdit_sourcefile.text())
                WavChecker.ORGPATHS = []
                self.wavchecker.start()
                self.pushButton_Start.setText("「Cancel..」")
                self.pushButton_AllReset.setEnabled(False)

            else:
                QMessageBox.critical(self, None,
                                     "ソースのパスが間違っています！\n正しく設定してください！",
                                     QMessageBox.Ok)

        else:
            QMessageBox.critical(self, None,
                                 "_CheckStartedのモードが存在しない内部矛盾だよ！サワツに連絡してね！",
                                 QMessageBox.Ok)

    def _AllReset(self):

        self.lineEdit_sourcefile.clear()
        self.label_sourceVideo.setText("..")
        self.label_sourceAudio.setText("..")
        # v141
        self.comboBox_sourcechannel.clear()
        self.comboBox_sourcechannel.hide()

        # 2ch
        self.lineEdit_2ch.clear()
        self.label_2chINFO.setText("..")

        # 5.1ch
        self.lineEdit_51ch_FL.clear()
        self.label_FLINFO.setText("..")
        self.lineEdit_51ch_FR.clear()
        self.label_FRINFO.setText("..")
        self.lineEdit_51ch_RL.clear()
        self.label_RLINFO.setText("..")
        self.lineEdit_51ch_RR.clear()
        self.label_RRINFO.setText("..")
        self.lineEdit_51ch_FC.clear()
        self.label_FCINFO.setText("..")
        self.lineEdit_51ch_LFE.clear()
        self.label_LFEINFO.setText("..")

        # 8ch
        self.lineEdit_8ch_L.clear()
        self.label_LINFO.setText("..")
        self.lineEdit_8ch_R.clear()
        self.label_RINFO.setText("..")

        # progress
        self.progressBar_ffmpeg.setValue(0)
        self.progressBar_orgwav.setValue(0)
        self.progressBar_srcwav.setValue(0)

        # log
        self.plainTextEdit_log.clear()
        self.plainTextEdit_log.setStyleSheet("QPlainTextEdit {background-color:#FFFFFF;}")

        self.textEdit_errlog.clear()
        self.textEdit_errlog.setStyleSheet("QTextEdit {background-color: #FFFFFF;color: #000000}")

        self.label_errlog.hide()
        self.textEdit_errlog.hide()

        self.source_audioformatdict.clear()
        self.original_audioformatdict.clear()

        self.lineEdit_videoin.clear()
        self.lineEdit_videohonben.clear()
        self.groupBox_videoinout.setChecked(False)
        self.groupBox_videoinout.setDisabled(True)

        self.checkBox_force16bit.setChecked(False)
        # v113
        self.checkBox_cinex.setChecked(False)

        self.wavchecker.opdict.clear()

        self.sourcevideoisdrop = None

        self.__hide_videoinout(False)

    def finishThread(self):

        self.__setprogress()
        self.progressBar_ffmpeg.setValue(self.progressBar_ffmpeg.maximum())
        self.progressBar_srcwav.setValue(self.progressBar_srcwav.maximum())
        self.progressBar_orgwav.setValue(self.progressBar_orgwav.maximum())
        self.__wavchecker_msgread()

        if WavChecker.CHECKEDSTATUS == 0:
            self.textEdit_errlog.setStyleSheet("QTextEdit {background-color: #FF0000;color: #FFFFFF}")
            self.plainTextEdit_log.setStyleSheet("QPlainTextEdit {background-color: #90ee90;}")

        elif WavChecker.CHECKEDSTATUS == 1:
            # Warn
            self.textEdit_errlog.setStyleSheet("QTextEdit {background-color: #FFFF00;color: #000000}")
            self.label_errlog.show()
            self.textEdit_errlog.show()

        else:
            # Error
            self.textEdit_errlog.setStyleSheet("QTextEdit {background-color: #FF0000;color: #FFFFFF}")
            self.label_errlog.show()
            self.textEdit_errlog.show()

        self.status_label.setText(WavChecker.STATUSMESSAGE)
        self.pushButton_Start.setText("「Start Check」")
        self.pushButton_AllReset.setEnabled(True)

    def timerEvent(self, tevent):

        if (tevent.timerId() == self.timerid):
            # If Thread keeps crashing in debug, it's a good idea to comment out __setprogress.
            self.__setprogress()
            self.__wavchecker_msgread()

        dotstr = ""
        for i in range(self.dot_count):
            # print(i)
            dotstr += "."
        self.status_label.setText(WavChecker.STATUSMESSAGE + dotstr)
        self.dot_count += 1

        if (self.dot_count == 4):
            self.dot_count = 0

    def __wavchecker_msgread(self):
        if (WavChecker.msgtrylock(self)):
            msg = WavChecker.msgread(self)
            if msg:
                self.plainTextEdit_log.moveCursor(QTextCursor.End)
                self.plainTextEdit_log.insertPlainText(msg)
                self.plainTextEdit_log.moveCursor(QTextCursor.End)
                WavChecker.msgclear(self)
            errmsg = WavChecker.msgread_error(self)
            if errmsg:
                self.textEdit_errlog.append(errmsg)
                WavChecker.msgclear_error(self)

            WavChecker.msgunlock(self)

    def __getbit_str(self, strdata):
        if strdata:
            bits_str = re.findall('pcm_[sf][1-9]+le', strdata)
            if bits_str:
                return bits_str[0]
            else:
                return None
        return

    def __setprogress(self):

        # If it is less than INT_MAX -2, treat it as is, but if it exceeds INT_MAX,
        # keep it within the INT_MAX range for progressBar settings.

        try:

            if WavChecker.PROGRESS_MAX_ORGWAV and WavChecker.PROGRESS_ORGWAV:
                if WavChecker.PROGRESS_MAX_ORGWAV < 2147483645:
                    self.progressBar_orgwav.setMaximum(WavChecker.PROGRESS_MAX_ORGWAV)
                    self.progressBar_orgwav.setValue(WavChecker.PROGRESS_ORGWAV)
                else:
                    self.progressBar_orgwav.setMaximum(int(WavChecker.PROGRESS_MAX_ORGWAV / 1000))
                    self.progressBar_orgwav.setValue(int(WavChecker.PROGRESS_ORGWAV / 1000))
        except OverflowError as e:
            self.progressBar_orgwav.setMaximum(int(WavChecker.PROGRESS_MAX_ORGWAV / 1000))
            self.progressBar_orgwav.setValue(int(WavChecker.PROGRESS_ORGWAV / 1000))

        # Measures to prevent the bar from fluctuating when setValue and tMaximum are set to 0,0 for progressBar
        # Set only when non-zero
        # print("WavChecker.PROGRESS_MAX_FFMPEG" + str(WavChecker.PROGRESS_MAX_FFMPEG))
        # print("PROGRESS_FFMPEG_SRC" + str(WavChecker.PROGRESS_FFMPEG_SRC))
        # print("PROGRESS_FFMPEG_ORG" + str(WavChecker.PROGRESS_FFMPEG_ORG))

        try:

            if WavChecker.PROGRESS_FFMPEG_SRC + WavChecker.PROGRESS_FFMPEG_ORG < 2147483645:
                self.progressBar_ffmpeg.setMaximum(WavChecker.PROGRESS_MAX_FFMPEG)
                self.progressBar_ffmpeg.setValue(WavChecker.PROGRESS_FFMPEG_SRC + WavChecker.PROGRESS_FFMPEG_ORG)
            else:
                self.progressBar_ffmpeg.setMaximum(WavChecker.PROGRESS_MAX_FFMPEG / 1000)
                self.progressBar_ffmpeg.setValue((WavChecker.PROGRESS_FFMPEG_SRC / 1000) + (WavChecker.PROGRESS_FFMPEG_ORG / 1000))
                # debug
                # print("PROGRESS_MAX_FFMPEG:{0} PROGRESS_FFMPEG_SRC:{1} PROGRESS_FFMPEG_ORG{2}".format(
                #     WavChecker.PROGRESS_MAX_FFMPEG,
                #     WavChecker.PROGRESS_FFMPEG_SRC,
                #     WavChecker.PROGRESS_FFMPEG_ORG
                # ))

        except OverflowError as e:
            self.progressBar_ffmpeg.setMaximum(WavChecker.PROGRESS_MAX_FFMPEG / 1000)
            self.progressBar_ffmpeg.setValue((WavChecker.PROGRESS_FFMPEG_SRC / 1000) + (WavChecker.PROGRESS_FFMPEG_ORG / 1000))

        try:

            if WavChecker.PROGRESS_MAX_SRCWAV and WavChecker.PROGRESS_SRCWAV:
                if WavChecker.PROGRESS_MAX_SRCWAV < 2147483645:
                    self.progressBar_srcwav.setMaximum(WavChecker.PROGRESS_MAX_SRCWAV)
                    self.progressBar_srcwav.setValue(WavChecker.PROGRESS_SRCWAV)
                else:
                    self.progressBar_srcwav.setMaximum(int(WavChecker.PROGRESS_MAX_SRCWAV / 1000))
                    self.progressBar_srcwav.setValue(int(WavChecker.PROGRESS_SRCWAV / 1000))

        except OverflowError as e:
            self.progressBar_srcwav.setMaximum(int(WavChecker.PROGRESS_MAX_SRCWAV / 1000))
            self.progressBar_srcwav.setValue(int(WavChecker.PROGRESS_SRCWAV / 1000))

    @QtCore.Slot()
    def beginTimer(self, last=False):
        self.timerid = QObject.startTimer(self, 2000)
        self.lasttimer = last

    @QtCore.Slot()
    def stopTimer(self):
        QObject.killTimer(self, self.timerid)

    def SourceOrgWavselected(self, filePath=None, lineedit=None, label=None, issource = False):

        # print("SourceOrgWavselected called")
        sender = self.sender()
        hasvideo = False

        fpsstr = None
        tcstr = None

        if sender == self.pushButton_sourceQT:
            lineedit = self.lineEdit_sourcefile
            label = self.label_sourceVideo
            issource = True # 1.0.1
        elif sender == self.pushButton_2ch:
            lineedit = self.lineEdit_2ch
            label = self.label_2chINFO
        elif sender == self.pushButton_51ch_FL:
            lineedit = self.lineEdit_51ch_FL
            label = self.label_FLINFO
        elif sender == self.pushButton_51ch_FR:
            lineedit = self.lineEdit_51ch_FR
            label = self.label_FRINFO
        elif sender == self.pushButton_51ch_RL:
            lineedit = self.lineEdit_51ch_RL
            label = self.label_RLINFO
        elif sender == self.pushButton_51ch_RR:
            lineedit = self.lineEdit_51ch_RR
            label = self.label_RRINFO
        elif sender == self.pushButton_51ch_FC:
            lineedit = self.lineEdit_51ch_FC
            label = self.label_FCINFO
        elif sender == self.pushButton_51ch_LFE:
            lineedit = self.lineEdit_51ch_LFE
            label = self.label_LFEINFO
        elif sender == self.pushButton_8ch_L:
            lineedit = self.lineEdit_8ch_L
            label = self.label_LINFO
        elif sender == self.pushButton_8ch_R:
            lineedit = self.lineEdit_8ch_R
            label = self.label_RINFO
        else:
            # D&D
            pass

        if filePath:
            fileName = filePath
        else:
            if label == self.label_sourceVideo:
                fileNamelist = QFileDialog.getOpenFileName(self, self.tr("Select file"),
                                                           selectedFilter="file (*.mov *.wav *.mxf)")
            else:
                fileNamelist = QFileDialog.getOpenFileName(self, self.tr("Select file"),
                                                           selectedFilter="file (*.mov *.wav *.mxf)")
            if fileNamelist:
                fileName = fileNamelist[0]

                # File Dialog cancel ?
                if not fileName:
                    return
            else:
                return

        hasvideo = False

        self.wavchecker.ffprobe_command(fileName)
        # self.plainTextEdit_log.appendPlainText("WavChecker" + self.__version__ + "\n")

        # org label
        if label:

            audio_streamno = 0
            predict_totalwavfilesize = 0 # for ffmpeg progress
            tcset_video = False
            tcset_audio = False

            ffprobestr_video = ""
            ffprobestr_audio = ""
            ffprobe_audiojsondict = {}

            for stream in self.wavchecker.ffprobe_streamsdict:

                # video stream
                if stream["codec_type"] == 'video':

                    hasvideo = True
                    # "prores" + "HQ"

                    ffprobestr_video += stream["codec_name"] + stream["profile"] + " "
                    # '2997/100' -> [0]='2997' [1]='100'
                    frameratelist = stream["r_frame_rate"].split("/")
                    fpsstr = '{:.2f}'.format(float(frameratelist[0]) / float(frameratelist[1]))

                    # 1000/1 time add?
                    if fpsstr == '29.97' or fpsstr == '23.98':
                        # self.wavchecker.opdict[self.wavchecker.OPDICT_VIDEOISDROP] = True
                        self.sourceisthousand = True
                    else:
                        self.sourceisthousand = False
                    ffprobestr_video += fpsstr + "fps "

                    if "nb_read_frames" in stream:
                        # In the case of h264, this seems to be the correct number of frames.
                        ffprobestr_video += stream["nb_read_frames"] + "Frames(nb_read_frames) "
                    elif "nb_frames" in stream:
                        ffprobestr_video += stream["nb_frames"] + "Frames(nb_frames) "
                    else:
                        pass

                    if "tags" in stream:
                        if isinstance(stream["tags"], dict):
                            tagsdict = stream["tags"]
                            if tagsdict.get("timecode"):
                                #V130
                                ffprobestr_video += "\nTC:" + tagsdict["timecode"]
                                # is non drop ?
                                if tagsdict["timecode"][-3] == ':':
                                    ffprobestr_video += "(NDF)"
                                else:
                                    # drop
                                    ffprobestr_video += "(DF)"
                            tcset_video = True
                # audio stream
                if stream["codec_type"] == 'audio':

                    if audio_streamno == 0:
                        ffprobe_audiojsondict = stream

                    ffprobestr_audio += "index:" + str(stream["index"]) + " "
                    ffprobestr_audio += stream["codec_name"] + " " + str(stream["bits_per_sample"]) + "bit "
                    ffprobestr_audio += str(int(stream["sample_rate"]) / 1000) + "khz "
                    ffprobestr_audio += str(stream["channels"]) + "channel(s) "

                    audio_streamno += stream["channels"]

                    samplenum = 0

                    if "channel_layout" in stream:
                        ffprobestr_audio += str(stream["channel_layout"]) + " "
                    if "nb_read_frames" in stream:
                        ffprobestr_audio += stream["nb_read_frames"] + "Samples(nb_read_frames) "
                        samplenum = int(stream["nb_read_frames"])
                    elif "nb_frames" in stream:
                        ffprobestr_audio += stream["nb_frames"] + "Samples(nb_frames) "
                        samplenum = int(stream["nb_frames"])
                    elif "duration_ts" in stream:
                        ffprobestr_audio += str(stream["duration_ts"]) + "Samples "
                        samplenum = int(stream["duration_ts"])
                    else:
                        pass

                    predict_totalwavfilesize += (int(stream["bits_per_sample"] / 8) * int(stream["channels"]) * samplenum)

                    if label == self.label_sourceVideo:
                        self.wavchecker.opdict[self.wavchecker.OPDICT_SRCWAVFILESIZE] = predict_totalwavfilesize

                        # print("OPDICT_SRCWAVFILESIZE" + str(self.wavchecker.opdict[self.wavchecker.OPDICT_SRCWAVFILESIZE]))
                    if label == self.label_2chINFO:
                        self.wavchecker.opdict[self.wavchecker.OPDICT_ORGWAVFILESIZE] = predict_totalwavfilesize
                        # print("OPDICT_ORGWAVFILESIZE" + str(self.wavchecker.opdict[self.wavchecker.OPDICT_ORGWAVFILESIZE]))
                    if "tags" in stream:
                        if isinstance(stream["tags"], dict):
                            tagsdict = stream["tags"]
                            if tagsdict.get("timecode"):
                                # is non drop ?
                                if tagsdict["timecode"][-3] == ':':
                                    ffprobestr_audio += "\n TC:" + tagsdict["timecode"] + "(NDF)"
                                else:
                                    # drop
                                    ffprobestr_audio += "\n TC:" + tagsdict["timecode"] + "(DF)"
                                tcset_audio = True
                    ffprobestr_audio += "\n"

                if stream["codec_type"] == 'data':
                    if isinstance(stream["tags"], dict):
                        tagsdict = stream["tags"]
                        if tagsdict.get("timecode"):

                            tcstr = str(tagsdict.get("timecode"))
                            self.wavchecker.opdict[self.wavchecker.OPDICT_STARTTC] = tcstr
                            if tcstr[-3] == ':':
                                # v141
                                tcstr = " TC:" + tcstr + "(NDF)\n"
                            else:
                                # v141
                                tcstr = " TC:" + tcstr + "(DF)\n"

                            if not tcset_video:
                                ffprobestr_video += tcstr
                                tcset_video = True
                            if not tcset_audio:
                                ffprobestr_audio += tcstr
                                tcset_audio = True

            if self.wavchecker.ffprobe_formatdict:
                formatdict = self.wavchecker.ffprobe_formatdict
                if formatdict.get("tags"):
                    tagdict = formatdict.get("tags")
                    encoder_str = str(tagdict.get("encoder"))
                    if encoder_str.startswith(self.wavchecker.RESOLVE_TAGS_AUDIO_HANDLER_NAME):
                        self.wavchecker.opdict[
                            self.wavchecker.OPDICT_SOURCEQTISRESOLVE] = self.wavchecker.RESOLVE_TAGS_AUDIO_HANDLER_NAME
                        QMessageBox.warning(self, None,
                                            "Resolveでエクスポートされてるwavを検知した！\nResolveはアタマとケツを勝手にフェードするのでエラーになる可能性があるぞ！",
                                            QMessageBox.Ok)

                    tcstr = tagdict.get("timecode")
                    if tcstr and not tcset_audio:
                        printtcstr = ""
                        if tcstr[-3] == ':':
                            # v141
                            printtcstr = " TC:" + tcstr + "(NDF)\n"
                        else:
                            # v141
                            printtcstr = " TC:" + tcstr + "(DF)\n"

                        ffprobestr_audio += printtcstr

            if issource:
                self.label_sourceAudio.setText(ffprobestr_audio)
                self.source_audioformatdict = copy.deepcopy(ffprobe_audiojsondict)
                self.source_audioformatdict["audio_streamno"] = audio_streamno
                if hasvideo:
                    self.label_sourceVideo.setText(ffprobestr_video)
                    # opdict fps set ?
                    self.wavchecker.opdict[self.wavchecker.OPDICT_FPS] = fpsstr

                else:
                    # no video information set to 29.974 virtual fps
                    # opdict fps virtual (29.97fps) set
                    self.wavchecker.opdict[self.wavchecker.OPDICT_FPS] = "29.97"
                    self.label_sourceVideo.clear()

                if tcstr:
                    self.wavchecker.opdict[self.wavchecker.OPDICT_STARTTC] = tcstr
                # v121
                elif self.wavchecker.opdict.get(self.wavchecker.OPDICT_STARTTC):
                    pass
                else:
                    self.wavchecker.opdict[self.wavchecker.OPDICT_STARTTC] = "00:00:00:00"
                    # v141 SAWA
                    self.wavchecker.opdict[self.wavchecker.OPDICT_STARTTCISNONE] = True
            else:

                if self.comboBox_source.currentIndex() == 0 or self.comboBox_source.currentIndex() == 4:
                    if label == self.label_2chINFO:
                        wkstr = ""
                        if hasvideo:
                            wkstr = "Video:" + ffprobestr_video + "\n"
                        wkstr += "Audio:\n" + ffprobestr_audio
                        label.setText(wkstr)
                        # print(wkstr)
                else:
                    label.setText(ffprobestr_audio)
                # original
                self.original_audioformatdict = copy.deepcopy(ffprobe_audiojsondict)
                self.original_audioformatdict["audio_streamno"] = audio_streamno

            # The longer duration is always remembered.
            curr_duration = self.wavchecker.opdict.get(self.wavchecker.OPDICT_MAXDURATION)
            if curr_duration is None or curr_duration < float(stream["duration"]):
                # max duration update.
                self.wavchecker.opdict[self.wavchecker.OPDICT_MAXDURATION] = float(stream["duration"])

        if lineedit:
            lineedit.setText(fileName)
            if lineedit == self.lineEdit_sourcefile:
                self.groupBox_videoinout.setEnabled(hasvideo)

        # V130
        if self.comboBox_source.currentIndex() == 0 and lineedit == self.lineEdit_sourcefile:
            self.__show_selectstream()

        # metadata difference check.
        errstr = self.CheckAudioMetaData(self.source_audioformatdict, self.original_audioformatdict)

        # some one exists error?
        if errstr:
            # warning
            QMessageBox.warning(None, None, errstr, QMessageBox.Ok)

        self.__wavchecker_msgread()


    def CheckAudioMetaData(self, sourcedict, originaldict):

        # Can't compare because either source or original is not entered?
        if not sourcedict or not originaldict:
            return None

        # set min audio stream num.
        if self.source_audioformatdict.get("audio_streamno") < self.original_audioformatdict.get("audio_streamno"):
            self.wavchecker.opdict[self.wavchecker.OPDICT_MINWAVCHNUM] = self.source_audioformatdict["audio_streamno"]
        else:
            self.wavchecker.opdict[self.wavchecker.OPDICT_MINWAVCHNUM] = self.original_audioformatdict["audio_streamno"]

        # v113
        if self.source_audioformatdict.get("audio_streamno") > self.original_audioformatdict.get("audio_streamno"):
            self.wavchecker.opdict[self.wavchecker.OPDICT_MAXWAVCHNUM] = self.source_audioformatdict["audio_streamno"]
        else:
            self.wavchecker.opdict[self.wavchecker.OPDICT_MAXWAVCHNUM] = self.original_audioformatdict["audio_streamno"]

        if not sourcedict.get("codec_name").startswith("pcm"):
            return ("ソースのオーディオフォーマットがPCMではありません！source = {0}".format \
                        (sourcedict.get("codec_name"),))

        if not originaldict.get("codec_name").startswith("pcm"):
            return ("オリジナルのオーディオフォーマットがPCMではありません！original = {0}".format \
                        (sourcedict.get("codec_name"),))

        # codec_name difference？ ex: "pcm_s24le" vs "pcm_s16le"
        if sourcedict.get("codec_name") != originaldict.get("codec_name"):

            # The audio format of QT output from baselight is big endian, so if it is not used as is,
            # A warning is issued because it cannot be compared with MA's little endian.
            # Analyze the content tag and do not display a warning if it has the characteristics of baselight.
            if sourcedict.get("tags"):
                tagsdict = sourcedict.get("tags")
                if tagsdict.get("handler_name") == self.wavchecker.BASELIGHT_TAGS_AUDIO_HANDLER_NAME:
                    self.wavchecker.opdict[self.wavchecker.OPDICT_SOURCEQTISBASELIGHT] = self.wavchecker.BASELIGHT_TAGS_AUDIO_HANDLER_NAME
            else:
                return ("ソースとオリジナルのコーデック名が一致しません！source = {0} original = {1}".format \
                            (sourcedict.get("codec_long_name"), originaldict.get("codec_long_name")))
        else:
            # Delete if there is a QT flag issued from baselight.
            self.wavchecker.opdict.pop(self.wavchecker.OPDICT_SOURCEQTISBASELIGHT, None)

        # bitdepth difference? ex: 24
        if str(sourcedict.get("bits_per_sample")) != str(originaldict.get("bits_per_sample")):

            srcbit = sourcedict.get("bits_per_sample")
            orgbit = originaldict.get("bits_per_sample")

            if self.checkBox_force16bit.isChecked() and orgbit is not None and orgbit != 16:
                return ("ソースを16bitダウンして比較するはずなのにオリジナルに16bit以外が指定されています！original = {0}bit".format \
                            (str(originaldict.get("bits_per_sample"))))
            elif self.checkBox_force16bit.isChecked() and orgbit == 16 and srcbit is not None:
                # src bit can't checked, pass
                pass
            else:
                return ("ソースとオリジナルのビットが異なっています！source = {0}bit original = {1}bit".format \
                            (str(sourcedict.get("bits_per_sample")), str(originaldict.get("bits_per_sample"))))
            # channel num difference? ex:1(mono) 2(stereo) 6(5.1ch) ....

        if self.comboBox_source.currentIndex() == 0:
            # Interleave mode
            if str(sourcedict.get("channels")) != str(originaldict.get("channels")):
                return ("ソースとオリジナルのチャネル数が異なっています！source = {0} original = {1}".format \
                            (str(sourcedict.get("channels")), str(originaldict.get("channels"))))

        elif self.comboBox_source.currentIndex() == 1:
            # 5.1ch mode
            # Source QT or wav channel is not 6 ?(5.1ch channel require 6 mono wav)
            if str(sourcedict.get("channels")) != "6":
                return ("ソースのチャネル数がインタリーブ5.1chではありません！source channels = {0}".format \
                            (str(sourcedict.get("channels"))))
            # original wav channel is not 1,(mono wav required)
            if str(originaldict.get("channels")) != "1":
                return ("オリジナルに指定したwavのチャネル数が1(モノ)ではありません！original channels = {0}".format \
                            (str(originaldict.get("channels"))))

        elif self.comboBox_source.currentIndex() == 2:
            # 2ch multi mono mode

            if str(sourcedict.get("channels")) != "2":
                return ("ソースに指定したwavのチャネル数が2(インタリーブステレオ)ではありません！original channels = {0}".format \
                            (str(sourcedict.get("channels"))))

            # The number of wav channels specified in the original isn't 1.
            # should put each item one by one(mono wav)
            if str(originaldict.get("channels")) != "1":
                return ("オリジナルに指定したwavのチャネル数が1(モノ)ではありません！original channels = {0}".format \
                            (str(originaldict.get("channels"))))

        elif self.comboBox_source.currentIndex() == 3:

            # 8ch oa mode
            if str(sourcedict.get("channels")) != "1":
                return ("ソースのaudio stream内のチャネル数が1(モノ)ではありません！source streams = {0}".format \
                                         (str(sourcedict.get("streams"))))

            # sonohoka
            if str(originaldict.get("channels")) != "1":
                return ("オリジナルに指定したwavのチャネル数が1(モノ)ではありません！original channels = {0}".format \
                            (str(originaldict.get("channels"))))

        elif self.comboBox_source.currentIndex() == 4:

            # source multi mono, org interleave
            if str(sourcedict.get("channels")) != "1":
                return ("ソースのaudio stream内のチャネル数が1(モノ)ではありません！source streams = {0}".format \
                            (str(sourcedict.get("streams"))))

            if str(originaldict.get("channels")) == "1":

                return ("オリジナルのaudio stream内のチャネル数が2または6(5.1ch)ではありません！source streams = {0}".format \
                            (str(sourcedict.get("streams"))))

            if sourcedict.get("audio_streamno") != originaldict.get("audio_streamno"):
                return ("オーディオチャネル数が一致しないため、存在するチャネルの数だけ比較します。比較チャネル数 = {0}".format(
                         self.wavchecker.opdict[self.wavchecker.OPDICT_MINWAVCHNUM]))

        else:
            pass

        # sample rate difference? ex:"48000"
        if sourcedict.get("sample_rate") != originaldict.get("sample_rate"):
            return ("ソースとオリジナルのサンプルレートが異なっています！source = {0} original = {1}".format \
                        (sourcedict.get("sample_rate"), originaldict.get("sample_rate")))

        # Bitrate is not checked. channel_layout=unknown,
        # because it seems like the rate may change slightly.

        srcsample = 0
        orgsample = 0

        if sourcedict.get("nb_frames"):
            srcsample = int(sourcedict.get("nb_frames"))
        elif sourcedict.get("duration_ts"):
            srcsample = int(sourcedict.get("duration_ts"))
        else:
            pass

        if originaldict.get("nb_frames"):
            orgsample = int(originaldict.get("nb_frames"))
        elif originaldict.get("duration_ts"):
            orgsample = int(originaldict.get("duration_ts"))
        else:
            pass

        if srcsample != orgsample:
            return ("ソースとオリジナルのサンプル数が異なっています！\n source = {0}sample\noriginal = {1}sample".format \
                        (srcsample, orgsample))

        return None
    # V130
    def __show_selectstream(self):

        self.comboBox_sourcechannel.clear()

        if self.label_sourceAudio.text():
            astreams = self.label_sourceAudio.text().split("\n")
            if len(astreams) > 1:
                for astr in astreams:
                    if not astr.startswith(" TC") and len(astr) > 0:
                        self.comboBox_sourcechannel.addItem(astr)
                self.label_source_channel.show()
                self.comboBox_sourcechannel.show()
            else:
                self.comboBox_sourcechannel.clear()
                self.label_source_channel.hide()
                self.comboBox_sourcechannel.hide()

    # V130
    def __hide_selectstream(self):
        self.comboBox_sourcechannel.clear()
        self.comboBox_sourcechannel.hide()
        self.label_source_channel.hide()

    def __hide_videoinout(self, req_visible):

        self.label_videoin.setVisible(req_visible)
        self.label_videohonben.setVisible(req_visible)
        self.lineEdit_videoin.setVisible(req_visible)
        self.lineEdit_videohonben.setVisible(req_visible)
        self.checkBox_videoswapsrcorg.setVisible(req_visible)

    def __videoinout_changed(self, changedtext):
        sender = self.sender()
        if changedtext:
            if sender == self.lineEdit_videohonben:
                parsestrlist = self.lineEdit_videohonben.text().split(":")
                if self.isbsordel == False:
                    # print("lineEdit_videohonben changed = " + changedtext)

                    if len(parsestrlist) == 1:
                        if len(parsestrlist[0]) == 2:
                            self.lineEdit_videohonben.setText(self.lineEdit_videohonben.text() + ":")

                    elif len(parsestrlist) == 2:
                        if len(parsestrlist[1]) == 2:
                            self.lineEdit_videohonben.setText(self.lineEdit_videohonben.text() + ":")
                    else:
                        pass
                else:
                    # True
                    pass

        # print("isbsordel = " + str(self.isbsordel))

    def eventFilter(self, obj, event):

        if obj == self.lineEdit_videohonben:
            if self.groupBox_videoinout.isEnabled() and self.groupBox_videoinout.isChecked():

                if event.type() == QtCore.QEvent.KeyPress:
                    keyevent = event.key()

                    if keyevent == Qt.Key_Backspace or keyevent == Qt.Key_Delete:
                        self.isbsordel = True
                        # print("self.isbsordel = " + str(self.isbsordel))

                    elif keyevent in self.numkeylist:

                        parsestrlist = self.lineEdit_videohonben.text().split(":")

                        if len(parsestrlist) == 1 and len(parsestrlist[0]) == 2:
                            self.lineEdit_videohonben.setText(self.lineEdit_videohonben.text() + ":")
                            self.isbsordel = False
                        elif len(parsestrlist) == 2 and len(parsestrlist[1]) == 2:
                            self.lineEdit_videohonben.setText(self.lineEdit_videohonben.text() + ":")
                            self.isbsordel = False
                        else:
                            self.isbsordel = False
                    else:
                        pass
            return (False)
        return (False)

# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow_ui.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(899, 1183)
        MainWindow.setUnifiedTitleAndToolBarOnMac(True)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_4 = QGridLayout(self.centralwidget)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_debug = QGridLayout()
        self.gridLayout_debug.setObjectName(u"gridLayout_debug")
        self.label_debuglog = QLabel(self.centralwidget)
        self.label_debuglog.setObjectName(u"label_debuglog")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_debuglog.sizePolicy().hasHeightForWidth())
        self.label_debuglog.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(11)
        self.label_debuglog.setFont(font)

        self.gridLayout_debug.addWidget(self.label_debuglog, 1, 0, 1, 1)

        self.plainTextEdit_log = QPlainTextEdit(self.centralwidget)
        self.plainTextEdit_log.setObjectName(u"plainTextEdit_log")
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.plainTextEdit_log.sizePolicy().hasHeightForWidth())
        self.plainTextEdit_log.setSizePolicy(sizePolicy1)
        font1 = QFont()
        font1.setPointSize(10)
        self.plainTextEdit_log.setFont(font1)
        self.plainTextEdit_log.setUndoRedoEnabled(False)
        self.plainTextEdit_log.setReadOnly(True)
        self.plainTextEdit_log.setTextInteractionFlags(Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)

        self.gridLayout_debug.addWidget(self.plainTextEdit_log, 2, 0, 1, 1)

        self.label_errlog = QLabel(self.centralwidget)
        self.label_errlog.setObjectName(u"label_errlog")
        sizePolicy.setHeightForWidth(self.label_errlog.sizePolicy().hasHeightForWidth())
        self.label_errlog.setSizePolicy(sizePolicy)
        font2 = QFont()
        font2.setPointSize(12)
        self.label_errlog.setFont(font2)

        self.gridLayout_debug.addWidget(self.label_errlog, 3, 0, 1, 1)

        self.textEdit_errlog = QTextEdit(self.centralwidget)
        self.textEdit_errlog.setObjectName(u"textEdit_errlog")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.textEdit_errlog.sizePolicy().hasHeightForWidth())
        self.textEdit_errlog.setSizePolicy(sizePolicy2)

        self.gridLayout_debug.addWidget(self.textEdit_errlog, 4, 0, 1, 1)


        self.gridLayout_4.addLayout(self.gridLayout_debug, 0, 1, 1, 1)

        self.horizontalLayout_2pane = QHBoxLayout()
        self.horizontalLayout_2pane.setObjectName(u"horizontalLayout_2pane")
        self.groupBox_source = QGroupBox(self.centralwidget)
        self.groupBox_source.setObjectName(u"groupBox_source")
        font3 = QFont()
        font3.setPointSize(14)
        self.groupBox_source.setFont(font3)
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_source)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.gridLayout_source = QGridLayout()
        self.gridLayout_source.setObjectName(u"gridLayout_source")
        self.lineEdit_sourcefile = QLineEdit(self.groupBox_source)
        self.lineEdit_sourcefile.setObjectName(u"lineEdit_sourcefile")
        font4 = QFont()
        font4.setPointSize(13)
        self.lineEdit_sourcefile.setFont(font4)
        self.lineEdit_sourcefile.setClearButtonEnabled(True)

        self.gridLayout_source.addWidget(self.lineEdit_sourcefile, 1, 1, 1, 1)

        self.label_source_2 = QLabel(self.groupBox_source)
        self.label_source_2.setObjectName(u"label_source_2")
        font5 = QFont()
        font5.setPointSize(14)
        font5.setBold(True)
        self.label_source_2.setFont(font5)
        self.label_source_2.setLayoutDirection(Qt.LeftToRight)
        self.label_source_2.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout_source.addWidget(self.label_source_2, 0, 0, 1, 1, Qt.AlignRight)

        self.pushButton_sourceQT = QPushButton(self.groupBox_source)
        self.pushButton_sourceQT.setObjectName(u"pushButton_sourceQT")
        font6 = QFont()
        font6.setPointSize(13)
        font6.setBold(True)
        self.pushButton_sourceQT.setFont(font6)

        self.gridLayout_source.addWidget(self.pushButton_sourceQT, 1, 0, 1, 1)

        self.comboBox_source = QComboBox(self.groupBox_source)
        self.comboBox_source.addItem("")
        self.comboBox_source.addItem("")
        self.comboBox_source.addItem("")
        self.comboBox_source.addItem("")
        self.comboBox_source.addItem("")
        self.comboBox_source.addItem("")
        self.comboBox_source.setObjectName(u"comboBox_source")
        sizePolicy.setHeightForWidth(self.comboBox_source.sizePolicy().hasHeightForWidth())
        self.comboBox_source.setSizePolicy(sizePolicy)
        self.comboBox_source.setMaximumSize(QSize(16777215, 16777215))
        self.comboBox_source.setFont(font4)

        self.gridLayout_source.addWidget(self.comboBox_source, 0, 1, 1, 1)

        self.label_source_channel = QLabel(self.groupBox_source)
        self.label_source_channel.setObjectName(u"label_source_channel")
        self.label_source_channel.setFont(font2)

        self.gridLayout_source.addWidget(self.label_source_channel, 2, 0, 1, 1, Qt.AlignRight)

        self.comboBox_sourcechannel = QComboBox(self.groupBox_source)
        self.comboBox_sourcechannel.setObjectName(u"comboBox_sourcechannel")
        self.comboBox_sourcechannel.setFont(font2)

        self.gridLayout_source.addWidget(self.comboBox_sourcechannel, 2, 1, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_source)

        self.groupBox_sourceVideo = QGroupBox(self.groupBox_source)
        self.groupBox_sourceVideo.setObjectName(u"groupBox_sourceVideo")
        self.groupBox_sourceVideo.setMaximumSize(QSize(16777215, 200))
        font7 = QFont()
        font7.setPointSize(12)
        font7.setKerning(True)
        self.groupBox_sourceVideo.setFont(font7)
        self.groupBox_sourceVideo.setFlat(False)
        self.groupBox_sourceVideo.setCheckable(False)
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_sourceVideo)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_sourceVideo = QLabel(self.groupBox_sourceVideo)
        self.label_sourceVideo.setObjectName(u"label_sourceVideo")
        self.label_sourceVideo.setMaximumSize(QSize(16777215, 100))
        self.label_sourceVideo.setFont(font7)
        self.label_sourceVideo.setFrameShape(QFrame.StyledPanel)
        self.label_sourceVideo.setFrameShadow(QFrame.Plain)
        self.label_sourceVideo.setWordWrap(True)
        self.label_sourceVideo.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextEditable)

        self.verticalLayout_4.addWidget(self.label_sourceVideo)

        self.groupBox_videoinout = QGroupBox(self.groupBox_sourceVideo)
        self.groupBox_videoinout.setObjectName(u"groupBox_videoinout")
        self.groupBox_videoinout.setMaximumSize(QSize(16777215, 120))
        font8 = QFont()
        font8.setPointSize(11)
        font8.setKerning(True)
        self.groupBox_videoinout.setFont(font8)
        self.groupBox_videoinout.setFlat(False)
        self.groupBox_videoinout.setCheckable(True)
        self.groupBox_videoinout.setChecked(False)
        self.gridLayout_3 = QGridLayout(self.groupBox_videoinout)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_videohonben = QLabel(self.groupBox_videoinout)
        self.label_videohonben.setObjectName(u"label_videohonben")
        sizePolicy1.setHeightForWidth(self.label_videohonben.sizePolicy().hasHeightForWidth())
        self.label_videohonben.setSizePolicy(sizePolicy1)
        self.label_videohonben.setMaximumSize(QSize(180, 16777215))
        self.label_videohonben.setFont(font7)

        self.gridLayout_3.addWidget(self.label_videohonben, 0, 1, 1, 1)

        self.label_videoin = QLabel(self.groupBox_videoinout)
        self.label_videoin.setObjectName(u"label_videoin")
        self.label_videoin.setMaximumSize(QSize(140, 16777215))
        self.label_videoin.setFont(font7)

        self.gridLayout_3.addWidget(self.label_videoin, 0, 0, 1, 1)

        self.lineEdit_videoin = QLineEdit(self.groupBox_videoinout)
        self.lineEdit_videoin.setObjectName(u"lineEdit_videoin")
        sizePolicy3 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.lineEdit_videoin.sizePolicy().hasHeightForWidth())
        self.lineEdit_videoin.setSizePolicy(sizePolicy3)
        self.lineEdit_videoin.setMaximumSize(QSize(150, 16777215))
        self.lineEdit_videoin.setFont(font8)
        self.lineEdit_videoin.setInputMethodHints(Qt.ImhDigitsOnly)
        self.lineEdit_videoin.setFrame(True)

        self.gridLayout_3.addWidget(self.lineEdit_videoin, 1, 0, 1, 1)

        self.lineEdit_videohonben = QLineEdit(self.groupBox_videoinout)
        self.lineEdit_videohonben.setObjectName(u"lineEdit_videohonben")
        sizePolicy3.setHeightForWidth(self.lineEdit_videohonben.sizePolicy().hasHeightForWidth())
        self.lineEdit_videohonben.setSizePolicy(sizePolicy3)
        self.lineEdit_videohonben.setMaximumSize(QSize(180, 16777215))
        self.lineEdit_videohonben.setFont(font8)
        self.lineEdit_videohonben.setInputMethodHints(Qt.ImhDigitsOnly)

        self.gridLayout_3.addWidget(self.lineEdit_videohonben, 1, 1, 1, 1)

        self.checkBox_videoswapsrcorg = QCheckBox(self.groupBox_videoinout)
        self.checkBox_videoswapsrcorg.setObjectName(u"checkBox_videoswapsrcorg")
        font9 = QFont()
        font9.setPointSize(10)
        font9.setKerning(True)
        self.checkBox_videoswapsrcorg.setFont(font9)

        self.gridLayout_3.addWidget(self.checkBox_videoswapsrcorg, 1, 2, 1, 1)


        self.verticalLayout_4.addWidget(self.groupBox_videoinout)


        self.verticalLayout_2.addWidget(self.groupBox_sourceVideo)

        self.groupBox_audio = QGroupBox(self.groupBox_source)
        self.groupBox_audio.setObjectName(u"groupBox_audio")
        self.groupBox_audio.setMaximumSize(QSize(16777215, 220))
        self.groupBox_audio.setFont(font2)
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_audio)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.label_sourceAudio = QLabel(self.groupBox_audio)
        self.label_sourceAudio.setObjectName(u"label_sourceAudio")
        self.label_sourceAudio.setFrameShape(QFrame.StyledPanel)
        self.label_sourceAudio.setWordWrap(True)
        self.label_sourceAudio.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextEditable)

        self.verticalLayout_5.addWidget(self.label_sourceAudio)

        self.checkBox_force16bit = QCheckBox(self.groupBox_audio)
        self.checkBox_force16bit.setObjectName(u"checkBox_force16bit")
        self.checkBox_force16bit.setFont(font2)

        self.verticalLayout_5.addWidget(self.checkBox_force16bit)


        self.verticalLayout_2.addWidget(self.groupBox_audio)

        self.groupBox_original = QGroupBox(self.groupBox_source)
        self.groupBox_original.setObjectName(u"groupBox_original")
        sizePolicy4 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.groupBox_original.sizePolicy().hasHeightForWidth())
        self.groupBox_original.setSizePolicy(sizePolicy4)
        self.groupBox_original.setMinimumSize(QSize(0, 270))
        self.groupBox_original.setMaximumSize(QSize(16777215, 16777215))
        self.groupBox_original.setFont(font3)
        self.groupBox_original.setAcceptDrops(True)
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_original)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.checkBox_cinex = QCheckBox(self.groupBox_original)
        self.checkBox_cinex.setObjectName(u"checkBox_cinex")
        self.checkBox_cinex.setFont(font2)

        self.verticalLayout_3.addWidget(self.checkBox_cinex)

        self.stackedWidget = QStackedWidget(self.groupBox_original)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy4.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy4)
        self.stackedWidget.setMinimumSize(QSize(0, 250))
        self.stackedWidget.setMaximumSize(QSize(16777215, 16777215))
        self.stackedWidget.setFont(font2)
        self.page_2ch = QWidget()
        self.page_2ch.setObjectName(u"page_2ch")
        self.page_2ch.setAcceptDrops(True)
        self.gridLayout = QGridLayout(self.page_2ch)
        self.gridLayout.setObjectName(u"gridLayout")
        self.lineEdit_2ch = QLineEdit(self.page_2ch)
        self.lineEdit_2ch.setObjectName(u"lineEdit_2ch")
        sizePolicy.setHeightForWidth(self.lineEdit_2ch.sizePolicy().hasHeightForWidth())
        self.lineEdit_2ch.setSizePolicy(sizePolicy)
        self.lineEdit_2ch.setFont(font2)
        self.lineEdit_2ch.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout.addWidget(self.lineEdit_2ch, 0, 1, 1, 1)

        self.label_2chINFO = QLabel(self.page_2ch)
        self.label_2chINFO.setObjectName(u"label_2chINFO")
        sizePolicy.setHeightForWidth(self.label_2chINFO.sizePolicy().hasHeightForWidth())
        self.label_2chINFO.setSizePolicy(sizePolicy)
        self.label_2chINFO.setMinimumSize(QSize(0, 220))
        self.label_2chINFO.setMaximumSize(QSize(16777215, 16777215))
        self.label_2chINFO.setFont(font2)
        self.label_2chINFO.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout.addWidget(self.label_2chINFO, 1, 1, 1, 1)

        self.pushButton_2ch = QPushButton(self.page_2ch)
        self.pushButton_2ch.setObjectName(u"pushButton_2ch")
        sizePolicy5 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.pushButton_2ch.sizePolicy().hasHeightForWidth())
        self.pushButton_2ch.setSizePolicy(sizePolicy5)
        self.pushButton_2ch.setFont(font7)

        self.gridLayout.addWidget(self.pushButton_2ch, 0, 0, 1, 1)

        self.stackedWidget.addWidget(self.page_2ch)
        self.page_51ch = QWidget()
        self.page_51ch.setObjectName(u"page_51ch")
        self.page_51ch.setAcceptDrops(True)
        self.gridLayout_2 = QGridLayout(self.page_51ch)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_FLINFO = QLabel(self.page_51ch)
        self.label_FLINFO.setObjectName(u"label_FLINFO")
        self.label_FLINFO.setFont(font2)

        self.gridLayout_2.addWidget(self.label_FLINFO, 9, 1, 1, 1)

        self.label_FRINFO = QLabel(self.page_51ch)
        self.label_FRINFO.setObjectName(u"label_FRINFO")
        self.label_FRINFO.setFont(font2)

        self.gridLayout_2.addWidget(self.label_FRINFO, 11, 1, 1, 1)

        self.pushButton_51ch_RR = QPushButton(self.page_51ch)
        self.pushButton_51ch_RR.setObjectName(u"pushButton_51ch_RR")
        self.pushButton_51ch_RR.setFont(font2)

        self.gridLayout_2.addWidget(self.pushButton_51ch_RR, 15, 0, 1, 1)

        self.pushButton_8ch_L = QPushButton(self.page_51ch)
        self.pushButton_8ch_L.setObjectName(u"pushButton_8ch_L")
        self.pushButton_8ch_L.setFont(font2)

        self.gridLayout_2.addWidget(self.pushButton_8ch_L, 1, 0, 1, 1)

        self.label_RRINFO = QLabel(self.page_51ch)
        self.label_RRINFO.setObjectName(u"label_RRINFO")
        self.label_RRINFO.setFont(font2)

        self.gridLayout_2.addWidget(self.label_RRINFO, 16, 1, 1, 1)

        self.label_LINFO = QLabel(self.page_51ch)
        self.label_LINFO.setObjectName(u"label_LINFO")
        self.label_LINFO.setFont(font2)
        self.label_LINFO.setWordWrap(False)

        self.gridLayout_2.addWidget(self.label_LINFO, 2, 1, 1, 1)

        self.pushButton_51ch_RL = QPushButton(self.page_51ch)
        self.pushButton_51ch_RL.setObjectName(u"pushButton_51ch_RL")
        self.pushButton_51ch_RL.setFont(font2)

        self.gridLayout_2.addWidget(self.pushButton_51ch_RL, 12, 0, 1, 1)

        self.pushButton_51ch_LFE = QPushButton(self.page_51ch)
        self.pushButton_51ch_LFE.setObjectName(u"pushButton_51ch_LFE")
        self.pushButton_51ch_LFE.setFont(font2)

        self.gridLayout_2.addWidget(self.pushButton_51ch_LFE, 19, 0, 1, 1)

        self.lineEdit_51ch_RR = QLineEdit(self.page_51ch)
        self.lineEdit_51ch_RR.setObjectName(u"lineEdit_51ch_RR")
        self.lineEdit_51ch_RR.setFont(font2)
        self.lineEdit_51ch_RR.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.lineEdit_51ch_RR, 15, 1, 1, 1)

        self.pushButton_51ch_FC = QPushButton(self.page_51ch)
        self.pushButton_51ch_FC.setObjectName(u"pushButton_51ch_FC")
        self.pushButton_51ch_FC.setFont(font2)

        self.gridLayout_2.addWidget(self.pushButton_51ch_FC, 17, 0, 1, 1)

        self.lineEdit_51ch_FC = QLineEdit(self.page_51ch)
        self.lineEdit_51ch_FC.setObjectName(u"lineEdit_51ch_FC")
        self.lineEdit_51ch_FC.setFont(font2)
        self.lineEdit_51ch_FC.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.lineEdit_51ch_FC, 17, 1, 1, 1)

        self.label_FCINFO = QLabel(self.page_51ch)
        self.label_FCINFO.setObjectName(u"label_FCINFO")
        self.label_FCINFO.setFont(font2)

        self.gridLayout_2.addWidget(self.label_FCINFO, 18, 1, 1, 1)

        self.label_RLINFO = QLabel(self.page_51ch)
        self.label_RLINFO.setObjectName(u"label_RLINFO")
        self.label_RLINFO.setFont(font2)

        self.gridLayout_2.addWidget(self.label_RLINFO, 13, 1, 1, 1)

        self.pushButton_51ch_FR = QPushButton(self.page_51ch)
        self.pushButton_51ch_FR.setObjectName(u"pushButton_51ch_FR")
        self.pushButton_51ch_FR.setFont(font2)

        self.gridLayout_2.addWidget(self.pushButton_51ch_FR, 10, 0, 1, 1)

        self.lineEdit_51ch_FL = QLineEdit(self.page_51ch)
        self.lineEdit_51ch_FL.setObjectName(u"lineEdit_51ch_FL")
        self.lineEdit_51ch_FL.setFont(font2)
        self.lineEdit_51ch_FL.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.lineEdit_51ch_FL, 8, 1, 1, 1)

        self.label_LFEINFO = QLabel(self.page_51ch)
        self.label_LFEINFO.setObjectName(u"label_LFEINFO")
        self.label_LFEINFO.setFont(font2)

        self.gridLayout_2.addWidget(self.label_LFEINFO, 20, 1, 1, 1)

        self.label_RINFO = QLabel(self.page_51ch)
        self.label_RINFO.setObjectName(u"label_RINFO")
        self.label_RINFO.setFont(font2)
        self.label_RINFO.setWordWrap(False)

        self.gridLayout_2.addWidget(self.label_RINFO, 6, 1, 1, 1)

        self.lineEdit_8ch_L = QLineEdit(self.page_51ch)
        self.lineEdit_8ch_L.setObjectName(u"lineEdit_8ch_L")
        self.lineEdit_8ch_L.setFont(font2)
        self.lineEdit_8ch_L.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.lineEdit_8ch_L, 1, 1, 1, 1)

        self.lineEdit_51ch_RL = QLineEdit(self.page_51ch)
        self.lineEdit_51ch_RL.setObjectName(u"lineEdit_51ch_RL")
        self.lineEdit_51ch_RL.setFont(font2)
        self.lineEdit_51ch_RL.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.lineEdit_51ch_RL, 12, 1, 1, 1)

        self.pushButton_8ch_R = QPushButton(self.page_51ch)
        self.pushButton_8ch_R.setObjectName(u"pushButton_8ch_R")
        self.pushButton_8ch_R.setFont(font2)

        self.gridLayout_2.addWidget(self.pushButton_8ch_R, 5, 0, 1, 1)

        self.pushButton_51ch_FL = QPushButton(self.page_51ch)
        self.pushButton_51ch_FL.setObjectName(u"pushButton_51ch_FL")
        self.pushButton_51ch_FL.setFont(font2)

        self.gridLayout_2.addWidget(self.pushButton_51ch_FL, 8, 0, 1, 1)

        self.lineEdit_8ch_R = QLineEdit(self.page_51ch)
        self.lineEdit_8ch_R.setObjectName(u"lineEdit_8ch_R")
        self.lineEdit_8ch_R.setFont(font2)
        self.lineEdit_8ch_R.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.lineEdit_8ch_R, 5, 1, 1, 1)

        self.lineEdit_51ch_LFE = QLineEdit(self.page_51ch)
        self.lineEdit_51ch_LFE.setObjectName(u"lineEdit_51ch_LFE")
        self.lineEdit_51ch_LFE.setFont(font2)
        self.lineEdit_51ch_LFE.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.lineEdit_51ch_LFE, 19, 1, 1, 1)

        self.lineEdit_51ch_FR = QLineEdit(self.page_51ch)
        self.lineEdit_51ch_FR.setObjectName(u"lineEdit_51ch_FR")
        self.lineEdit_51ch_FR.setFont(font2)
        self.lineEdit_51ch_FR.setClearButtonEnabled(True)

        self.gridLayout_2.addWidget(self.lineEdit_51ch_FR, 10, 1, 1, 1)

        self.stackedWidget.addWidget(self.page_51ch)

        self.verticalLayout_3.addWidget(self.stackedWidget)


        self.verticalLayout_2.addWidget(self.groupBox_original)

        self.pushButton_Start = QPushButton(self.groupBox_source)
        self.pushButton_Start.setObjectName(u"pushButton_Start")
        sizePolicy5.setHeightForWidth(self.pushButton_Start.sizePolicy().hasHeightForWidth())
        self.pushButton_Start.setSizePolicy(sizePolicy5)
        self.pushButton_Start.setMaximumSize(QSize(300, 16777215))
        self.pushButton_Start.setFont(font6)

        self.verticalLayout_2.addWidget(self.pushButton_Start, 0, Qt.AlignHCenter)

        self.pushButton_AllReset = QPushButton(self.groupBox_source)
        self.pushButton_AllReset.setObjectName(u"pushButton_AllReset")
        sizePolicy5.setHeightForWidth(self.pushButton_AllReset.sizePolicy().hasHeightForWidth())
        self.pushButton_AllReset.setSizePolicy(sizePolicy5)
        self.pushButton_AllReset.setMaximumSize(QSize(220, 16777215))
        self.pushButton_AllReset.setFont(font2)

        self.verticalLayout_2.addWidget(self.pushButton_AllReset, 0, Qt.AlignHCenter)

        self.gridLayout_progress = QGridLayout()
        self.gridLayout_progress.setObjectName(u"gridLayout_progress")
        self.label_ffmpegprogress = QLabel(self.groupBox_source)
        self.label_ffmpegprogress.setObjectName(u"label_ffmpegprogress")

        self.gridLayout_progress.addWidget(self.label_ffmpegprogress, 0, 0, 1, 1)

        self.progressBar_orgwav = QProgressBar(self.groupBox_source)
        self.progressBar_orgwav.setObjectName(u"progressBar_orgwav")
        self.progressBar_orgwav.setValue(0)
        self.progressBar_orgwav.setTextVisible(True)

        self.gridLayout_progress.addWidget(self.progressBar_orgwav, 1, 1, 1, 1)

        self.label_srcwavprogress = QLabel(self.groupBox_source)
        self.label_srcwavprogress.setObjectName(u"label_srcwavprogress")

        self.gridLayout_progress.addWidget(self.label_srcwavprogress, 4, 0, 1, 1)

        self.progressBar_srcwav = QProgressBar(self.groupBox_source)
        self.progressBar_srcwav.setObjectName(u"progressBar_srcwav")
        self.progressBar_srcwav.setValue(0)

        self.gridLayout_progress.addWidget(self.progressBar_srcwav, 4, 1, 1, 1)

        self.progressBar_ffmpeg = QProgressBar(self.groupBox_source)
        self.progressBar_ffmpeg.setObjectName(u"progressBar_ffmpeg")
        self.progressBar_ffmpeg.setValue(0)
        self.progressBar_ffmpeg.setTextVisible(True)

        self.gridLayout_progress.addWidget(self.progressBar_ffmpeg, 0, 1, 1, 1)

        self.label_orgwavprogress = QLabel(self.groupBox_source)
        self.label_orgwavprogress.setObjectName(u"label_orgwavprogress")

        self.gridLayout_progress.addWidget(self.label_orgwavprogress, 1, 0, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_progress)


        self.horizontalLayout_2pane.addWidget(self.groupBox_source)


        self.gridLayout_4.addLayout(self.horizontalLayout_2pane, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 899, 24))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        QWidget.setTabOrder(self.comboBox_source, self.pushButton_sourceQT)
        QWidget.setTabOrder(self.pushButton_sourceQT, self.lineEdit_sourcefile)
        QWidget.setTabOrder(self.lineEdit_sourcefile, self.comboBox_sourcechannel)
        QWidget.setTabOrder(self.comboBox_sourcechannel, self.groupBox_videoinout)
        QWidget.setTabOrder(self.groupBox_videoinout, self.lineEdit_videoin)
        QWidget.setTabOrder(self.lineEdit_videoin, self.lineEdit_videohonben)
        QWidget.setTabOrder(self.lineEdit_videohonben, self.checkBox_videoswapsrcorg)
        QWidget.setTabOrder(self.checkBox_videoswapsrcorg, self.checkBox_force16bit)
        QWidget.setTabOrder(self.checkBox_force16bit, self.checkBox_cinex)
        QWidget.setTabOrder(self.checkBox_cinex, self.pushButton_8ch_L)
        QWidget.setTabOrder(self.pushButton_8ch_L, self.lineEdit_8ch_L)
        QWidget.setTabOrder(self.lineEdit_8ch_L, self.pushButton_8ch_R)
        QWidget.setTabOrder(self.pushButton_8ch_R, self.lineEdit_8ch_R)
        QWidget.setTabOrder(self.lineEdit_8ch_R, self.pushButton_51ch_FL)
        QWidget.setTabOrder(self.pushButton_51ch_FL, self.lineEdit_51ch_FL)
        QWidget.setTabOrder(self.lineEdit_51ch_FL, self.pushButton_51ch_FR)
        QWidget.setTabOrder(self.pushButton_51ch_FR, self.lineEdit_51ch_FR)
        QWidget.setTabOrder(self.lineEdit_51ch_FR, self.pushButton_51ch_RL)
        QWidget.setTabOrder(self.pushButton_51ch_RL, self.lineEdit_51ch_RL)
        QWidget.setTabOrder(self.lineEdit_51ch_RL, self.pushButton_51ch_RR)
        QWidget.setTabOrder(self.pushButton_51ch_RR, self.lineEdit_51ch_RR)
        QWidget.setTabOrder(self.lineEdit_51ch_RR, self.pushButton_51ch_FC)
        QWidget.setTabOrder(self.pushButton_51ch_FC, self.lineEdit_51ch_FC)
        QWidget.setTabOrder(self.lineEdit_51ch_FC, self.pushButton_51ch_LFE)
        QWidget.setTabOrder(self.pushButton_51ch_LFE, self.lineEdit_51ch_LFE)
        QWidget.setTabOrder(self.lineEdit_51ch_LFE, self.pushButton_2ch)
        QWidget.setTabOrder(self.pushButton_2ch, self.lineEdit_2ch)
        QWidget.setTabOrder(self.lineEdit_2ch, self.pushButton_Start)
        QWidget.setTabOrder(self.pushButton_Start, self.pushButton_AllReset)
        QWidget.setTabOrder(self.pushButton_AllReset, self.plainTextEdit_log)
        QWidget.setTabOrder(self.plainTextEdit_log, self.textEdit_errlog)

        self.retranslateUi(MainWindow)

        self.comboBox_source.setCurrentIndex(0)
        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"QTWAVChecker", None))
        self.label_debuglog.setText(QCoreApplication.translate("MainWindow", u"Debug Log:", None))
        self.plainTextEdit_log.setPlainText("")
        self.label_errlog.setText(QCoreApplication.translate("MainWindow", u"Error Log:", None))
        self.groupBox_source.setTitle(QCoreApplication.translate("MainWindow", u"Source Input/Information:", None))
        self.lineEdit_sourcefile.setText("")
        self.lineEdit_sourcefile.setPlaceholderText(QCoreApplication.translate("MainWindow", u"D&D QT or MXF or wav file.(source)", None))
        self.label_source_2.setText(QCoreApplication.translate("MainWindow", u"Mode:", None))
        self.pushButton_sourceQT.setText(QCoreApplication.translate("MainWindow", u"Source QT or wav", None))
        self.comboBox_source.setItemText(0, QCoreApplication.translate("MainWindow", u"Interleave <-> Interleave Mode", None))
        self.comboBox_source.setItemText(1, QCoreApplication.translate("MainWindow", u"Interleave5.1ch <-> Mono x 6 Mode", None))
        self.comboBox_source.setItemText(2, QCoreApplication.translate("MainWindow", u"Interleave2ch <-> Mono x2 Mode", None))
        self.comboBox_source.setItemText(3, QCoreApplication.translate("MainWindow", u"MultiMono <-> Mono x 2-8ch Mode(MXF_OA Mode)", None))
        self.comboBox_source.setItemText(4, QCoreApplication.translate("MainWindow", u"MultiMono <-> Interleave Mode(MXF_OA_Mode)", None))
        self.comboBox_source.setItemText(5, QCoreApplication.translate("MainWindow", u"Muon Check Mode", None))

        self.label_source_channel.setText(QCoreApplication.translate("MainWindow", u"SChannel select:", None))
        self.groupBox_sourceVideo.setTitle(QCoreApplication.translate("MainWindow", u"Video:", None))
        self.label_sourceVideo.setText(QCoreApplication.translate("MainWindow", u"..", None))
        self.groupBox_videoinout.setTitle(QCoreApplication.translate("MainWindow", u"Enable Head and Honben", None))
        self.label_videohonben.setText(QCoreApplication.translate("MainWindow", u"Honben hh:mm:ss", None))
        self.label_videoin.setText(QCoreApplication.translate("MainWindow", u"Head Cut second", None))
        self.lineEdit_videoin.setPlaceholderText(QCoreApplication.translate("MainWindow", u"set Head cut sec ex:10", None))
        self.lineEdit_videohonben.setText("")
        self.lineEdit_videohonben.setPlaceholderText(QCoreApplication.translate("MainWindow", u"set hh:mm:ss ex:2:12:33", None))
        self.checkBox_videoswapsrcorg.setText(QCoreApplication.translate("MainWindow", u"Swap src<->org", None))
        self.groupBox_audio.setTitle(QCoreApplication.translate("MainWindow", u"Audio:", None))
        self.label_sourceAudio.setText(QCoreApplication.translate("MainWindow", u"..", None))
        self.checkBox_force16bit.setText(QCoreApplication.translate("MainWindow", u"Force 16bit wav extract(for cinex insert)", None))
        self.groupBox_original.setTitle(QCoreApplication.translate("MainWindow", u"Original Input/Information", None))
        self.checkBox_cinex.setText(QCoreApplication.translate("MainWindow", u"cinex insert bug check", None))
        self.lineEdit_2ch.setText("")
        self.lineEdit_2ch.setPlaceholderText(QCoreApplication.translate("MainWindow", u"D&D or push \"Original wav\" button.", None))
        self.label_2chINFO.setText(QCoreApplication.translate("MainWindow", u"..", None))
        self.pushButton_2ch.setText(QCoreApplication.translate("MainWindow", u"Original wav", None))
        self.label_FLINFO.setText(QCoreApplication.translate("MainWindow", u"..", None))
        self.label_FRINFO.setText(QCoreApplication.translate("MainWindow", u"..", None))
        self.pushButton_51ch_RR.setText(QCoreApplication.translate("MainWindow", u"Rear Right:", None))
        self.pushButton_8ch_L.setText(QCoreApplication.translate("MainWindow", u"Left:", None))
        self.label_RRINFO.setText(QCoreApplication.translate("MainWindow", u"..", None))
        self.label_LINFO.setText(QCoreApplication.translate("MainWindow", u"..", None))
        self.pushButton_51ch_RL.setText(QCoreApplication.translate("MainWindow", u"Rear Left:", None))
        self.pushButton_51ch_LFE.setText(QCoreApplication.translate("MainWindow", u"LFE:", None))
        self.lineEdit_51ch_RR.setText("")
        self.lineEdit_51ch_RR.setPlaceholderText(QCoreApplication.translate("MainWindow", u"D&D or push \"Rear Right:\" original wav file(mono)", None))
        self.pushButton_51ch_FC.setText(QCoreApplication.translate("MainWindow", u"Front Center:", None))
        self.lineEdit_51ch_FC.setText("")
        self.lineEdit_51ch_FC.setPlaceholderText(QCoreApplication.translate("MainWindow", u"D&D or push \"Front Center:\" original wav file(mono)", None))
        self.label_FCINFO.setText(QCoreApplication.translate("MainWindow", u"..", None))
        self.label_RLINFO.setText(QCoreApplication.translate("MainWindow", u"..", None))
        self.pushButton_51ch_FR.setText(QCoreApplication.translate("MainWindow", u"Front Right:", None))
        self.lineEdit_51ch_FL.setText("")
        self.lineEdit_51ch_FL.setPlaceholderText(QCoreApplication.translate("MainWindow", u"D&D or push \"Front Left:\" original wav file(mono)", None))
        self.label_LFEINFO.setText(QCoreApplication.translate("MainWindow", u"..", None))
        self.label_RINFO.setText(QCoreApplication.translate("MainWindow", u"..", None))
        self.lineEdit_8ch_L.setText("")
        self.lineEdit_8ch_L.setPlaceholderText(QCoreApplication.translate("MainWindow", u"D&D or push \"Left:\" original wav file(mono)", None))
        self.lineEdit_51ch_RL.setText("")
        self.lineEdit_51ch_RL.setPlaceholderText(QCoreApplication.translate("MainWindow", u"D&D or push \"Rear Left:\" original wav file(mono)", None))
        self.pushButton_8ch_R.setText(QCoreApplication.translate("MainWindow", u"Right:", None))
        self.pushButton_51ch_FL.setText(QCoreApplication.translate("MainWindow", u"Front Left:", None))
        self.lineEdit_8ch_R.setText("")
        self.lineEdit_8ch_R.setPlaceholderText(QCoreApplication.translate("MainWindow", u"D&D or push \"Right:\" original wav file(mono)", u"D&D or push \"Right:\" original wav file(mono)"))
        self.lineEdit_51ch_LFE.setText("")
        self.lineEdit_51ch_LFE.setPlaceholderText(QCoreApplication.translate("MainWindow", u"D&D or push \"LFE\" original wav file(mono)", None))
        self.lineEdit_51ch_FR.setText("")
        self.lineEdit_51ch_FR.setPlaceholderText(QCoreApplication.translate("MainWindow", u"D&D or push \"Front Right:\" original wav file(mono)", None))
        self.pushButton_Start.setText(QCoreApplication.translate("MainWindow", u"\u300cStart Check \u300d", None))
        self.pushButton_AllReset.setText(QCoreApplication.translate("MainWindow", u"All Reset(Clear all input and Log)", None))
        self.label_ffmpegprogress.setText(QCoreApplication.translate("MainWindow", u"QT -> wav progress:", None))
        self.label_srcwavprogress.setText(QCoreApplication.translate("MainWindow", u"source wav check:", None))
        self.progressBar_ffmpeg.setFormat(QCoreApplication.translate("MainWindow", u"%p%", None))
        self.label_orgwavprogress.setText(QCoreApplication.translate("MainWindow", u"original wav check:", None))
    # retranslateUi


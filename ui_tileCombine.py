# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tileCombineonxzzq.ui'
##
## Created by: Qt User Interface Compiler version 5.15.15
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 829)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")

        self.horizontalLayout_5.addWidget(self.label)

        self.tileDirEdit = QLineEdit(self.centralwidget)
        self.tileDirEdit.setObjectName(u"tileDirEdit")

        self.horizontalLayout_5.addWidget(self.tileDirEdit)

        self.browseTileDirBtn = QPushButton(self.centralwidget)
        self.browseTileDirBtn.setObjectName(u"browseTileDirBtn")

        self.horizontalLayout_5.addWidget(self.browseTileDirBtn)


        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.xAxisGroup = QGroupBox(self.centralwidget)
        self.xAxisGroup.setObjectName(u"xAxisGroup")
        self.horizontalLayout = QHBoxLayout(self.xAxisGroup)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_2 = QLabel(self.xAxisGroup)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_4.addWidget(self.label_2)

        self.xStartEdit = QLineEdit(self.xAxisGroup)
        self.xStartEdit.setObjectName(u"xStartEdit")

        self.horizontalLayout_4.addWidget(self.xStartEdit)


        self.horizontalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_3)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_3 = QLabel(self.xAxisGroup)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_7.addWidget(self.label_3)

        self.xEndEdit = QLineEdit(self.xAxisGroup)
        self.xEndEdit.setObjectName(u"xEndEdit")

        self.horizontalLayout_7.addWidget(self.xEndEdit)


        self.horizontalLayout.addLayout(self.horizontalLayout_7)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_6)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_4 = QLabel(self.xAxisGroup)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_8.addWidget(self.label_4)

        self.xStepEdit = QLineEdit(self.xAxisGroup)
        self.xStepEdit.setObjectName(u"xStepEdit")

        self.horizontalLayout_8.addWidget(self.xStepEdit)


        self.horizontalLayout.addLayout(self.horizontalLayout_8)


        self.verticalLayout.addWidget(self.xAxisGroup)

        self.yAxisGroup = QGroupBox(self.centralwidget)
        self.yAxisGroup.setObjectName(u"yAxisGroup")
        self.horizontalLayout_2 = QHBoxLayout(self.yAxisGroup)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_5 = QLabel(self.yAxisGroup)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_3.addWidget(self.label_5)

        self.yStartEdit = QLineEdit(self.yAxisGroup)
        self.yStartEdit.setObjectName(u"yStartEdit")

        self.horizontalLayout_3.addWidget(self.yStartEdit)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_6 = QLabel(self.yAxisGroup)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_9.addWidget(self.label_6)

        self.yEndEdit = QLineEdit(self.yAxisGroup)
        self.yEndEdit.setObjectName(u"yEndEdit")

        self.horizontalLayout_9.addWidget(self.yEndEdit)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_9)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_5)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.label_7 = QLabel(self.yAxisGroup)
        self.label_7.setObjectName(u"label_7")

        self.horizontalLayout_10.addWidget(self.label_7)

        self.yStepEdit = QLineEdit(self.yAxisGroup)
        self.yStepEdit.setObjectName(u"yStepEdit")

        self.horizontalLayout_10.addWidget(self.yStepEdit)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_10)


        self.verticalLayout.addWidget(self.yAxisGroup)

        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.horizontalLayout_11 = QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.label_10 = QLabel(self.groupBox_2)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_11.addWidget(self.label_10)

        self.tileLengthLineEdit = QLineEdit(self.groupBox_2)
        self.tileLengthLineEdit.setObjectName(u"tileLengthLineEdit")

        self.horizontalLayout_11.addWidget(self.tileLengthLineEdit)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer)

        self.label_11 = QLabel(self.groupBox_2)
        self.label_11.setObjectName(u"label_11")

        self.horizontalLayout_11.addWidget(self.label_11)

        self.tileWidthLineEdit = QLineEdit(self.groupBox_2)
        self.tileWidthLineEdit.setObjectName(u"tileWidthLineEdit")

        self.horizontalLayout_11.addWidget(self.tileWidthLineEdit)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_2)

        self.label_71 = QLabel(self.groupBox_2)
        self.label_71.setObjectName(u"label_71")

        self.horizontalLayout_11.addWidget(self.label_71)

        self.tileChannelsLineEdit = QLineEdit(self.groupBox_2)
        self.tileChannelsLineEdit.setObjectName(u"tileChannelsLineEdit")

        self.horizontalLayout_11.addWidget(self.tileChannelsLineEdit)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_8 = QLabel(self.centralwidget)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_6.addWidget(self.label_8)

        self.saveFileEdit = QLineEdit(self.centralwidget)
        self.saveFileEdit.setObjectName(u"saveFileEdit")

        self.horizontalLayout_6.addWidget(self.saveFileEdit)

        self.browseSaveFileBtn = QPushButton(self.centralwidget)
        self.browseSaveFileBtn.setObjectName(u"browseSaveFileBtn")

        self.horizontalLayout_6.addWidget(self.browseSaveFileBtn)


        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_9 = QLabel(self.centralwidget)
        self.label_9.setObjectName(u"label_9")

        self.horizontalLayout_12.addWidget(self.label_9)

        self.nProcEdit = QLineEdit(self.centralwidget)
        self.nProcEdit.setObjectName(u"nProcEdit")

        self.horizontalLayout_12.addWidget(self.nProcEdit)

        self.processBtn = QPushButton(self.centralwidget)
        self.processBtn.setObjectName(u"processBtn")

        self.horizontalLayout_12.addWidget(self.processBtn)


        self.verticalLayout.addLayout(self.horizontalLayout_12)

        self.imageLabel = QLabel(self.centralwidget)
        self.imageLabel.setObjectName(u"imageLabel")
        self.imageLabel.setMinimumSize(QSize(300, 400))
        self.imageLabel.setFrameShape(QFrame.Box)
        self.imageLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.imageLabel)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u74e6\u7247\u56fe\u5408\u5e76\u5de5\u5177", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u74e6\u7247\u56fe\u6839\u76ee\u5f55\uff1a", None))
        self.tileDirEdit.setText(QCoreApplication.translate("MainWindow", u".\\satellite\\\u9ad8\u5fb7\u536b\u661f\u5f71\u50cf\\14", None))
        self.browseTileDirBtn.setText(QCoreApplication.translate("MainWindow", u"\u6d4f\u89c8...", None))
        self.xAxisGroup.setTitle(QCoreApplication.translate("MainWindow", u"x\u8f74/\u5217\u53f7", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"\u8d77\u59cb", None))
        self.xStartEdit.setText(QCoreApplication.translate("MainWindow", u"12904", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"\u7ec8\u6b62", None))
        self.xEndEdit.setText(QCoreApplication.translate("MainWindow", u"12922", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"\u6b65\u957f", None))
        self.xStepEdit.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.yAxisGroup.setTitle(QCoreApplication.translate("MainWindow", u"y\u8f74/\u884c\u53f7", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"\u8d77\u59cb", None))
        self.yStartEdit.setText(QCoreApplication.translate("MainWindow", u"6424", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"\u7ec8\u6b62", None))
        self.yEndEdit.setText(QCoreApplication.translate("MainWindow", u"6431", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"\u6b65\u957f", None))
        self.yStepEdit.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"\u74e6\u7247\u5c5e\u6027", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"\u957f\u5ea6", None))
        self.tileLengthLineEdit.setText(QCoreApplication.translate("MainWindow", u"256", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"\u5bbd\u5ea6", None))
        self.tileWidthLineEdit.setText(QCoreApplication.translate("MainWindow", u"256", None))
        self.label_71.setText(QCoreApplication.translate("MainWindow", u"\u901a\u9053", None))
        self.tileChannelsLineEdit.setText(QCoreApplication.translate("MainWindow", u"3", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"\u4fdd\u5b58\u6587\u4ef6\uff1a", None))
        self.saveFileEdit.setText(QCoreApplication.translate("MainWindow", u".\\satellite\\\u9ad8\u5fb7\u536b\u661f\u5f71\u50cf\\14\\integrate.png", None))
        self.browseSaveFileBtn.setText(QCoreApplication.translate("MainWindow", u"\u6d4f\u89c8...", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"\u8fdb\u7a0b\u6570\uff1a", None))
        self.nProcEdit.setText(QCoreApplication.translate("MainWindow", u"8", None))
        self.processBtn.setText(QCoreApplication.translate("MainWindow", u"\u5f00\u59cb\u5904\u7406", None))
        self.imageLabel.setText(QCoreApplication.translate("MainWindow", u"\u8fdb\u5ea6\u5c55\u793a\u533a\u57df", None))
    # retranslateUi


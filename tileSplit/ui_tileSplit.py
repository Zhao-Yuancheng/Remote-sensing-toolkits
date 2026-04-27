# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tileSplitNMPyiM.ui'
##
## Created by: Qt User Interface Compiler version 5.15.15
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 772)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_8 = QLabel(self.centralwidget)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_6.addWidget(self.label_8)

        self.openFileEdit = QLineEdit(self.centralwidget)
        self.openFileEdit.setObjectName(u"openFileEdit")

        self.horizontalLayout_6.addWidget(self.openFileEdit)

        self.browseOpenFileBtn = QPushButton(self.centralwidget)
        self.browseOpenFileBtn.setObjectName(u"browseOpenFileBtn")

        self.horizontalLayout_6.addWidget(self.browseOpenFileBtn)


        self.verticalLayout.addLayout(self.horizontalLayout_6)

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

        self.tileHeightLineEdit = QLineEdit(self.groupBox_2)
        self.tileHeightLineEdit.setObjectName(u"tileHeightLineEdit")

        self.horizontalLayout_11.addWidget(self.tileHeightLineEdit)

        self.label_11 = QLabel(self.groupBox_2)
        self.label_11.setObjectName(u"label_11")

        self.horizontalLayout_11.addWidget(self.label_11)

        self.tileWidthLineEdit = QLineEdit(self.groupBox_2)
        self.tileWidthLineEdit.setObjectName(u"tileWidthLineEdit")

        self.horizontalLayout_11.addWidget(self.tileWidthLineEdit)


        self.verticalLayout.addWidget(self.groupBox_2)

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

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_9 = QLabel(self.centralwidget)
        self.label_9.setObjectName(u"label_9")

        self.horizontalLayout_12.addWidget(self.label_9)

        self.nProcEdit = QLineEdit(self.centralwidget)
        self.nProcEdit.setObjectName(u"nProcEdit")

        self.horizontalLayout_12.addWidget(self.nProcEdit)

        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_12.addWidget(self.label_3)

        self.resultFormatComboBox = QComboBox(self.centralwidget)
        self.resultFormatComboBox.addItem("")
        self.resultFormatComboBox.addItem("")
        self.resultFormatComboBox.addItem("")
        self.resultFormatComboBox.addItem("")
        self.resultFormatComboBox.addItem("")
        self.resultFormatComboBox.addItem("")
        self.resultFormatComboBox.setObjectName(u"resultFormatComboBox")

        self.horizontalLayout_12.addWidget(self.resultFormatComboBox)

        self.processBtn = QPushButton(self.centralwidget)
        self.processBtn.setObjectName(u"processBtn")

        self.horizontalLayout_12.addWidget(self.processBtn)


        self.verticalLayout.addLayout(self.horizontalLayout_12)

        self.imageLabel = QLabel(self.centralwidget)
        self.imageLabel.setObjectName(u"imageLabel")
        self.imageLabel.setMinimumSize(QSize(300, 400))
        self.imageLabel.setAutoFillBackground(False)
        self.imageLabel.setStyleSheet(u"background-color:rgb(220, 220, 220)")
        self.imageLabel.setFrameShape(QFrame.Box)
        self.imageLabel.setFrameShadow(QFrame.Plain)
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
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u74e6\u7247\u56fe\u751f\u6210\u5de5\u5177", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"\u6253\u5f00\u9065\u611f\u56fe\u50cf\uff1a", None))
        self.openFileEdit.setText("")
        self.browseOpenFileBtn.setText(QCoreApplication.translate("MainWindow", u"\u6d4f\u89c8...", None))
        self.xAxisGroup.setTitle(QCoreApplication.translate("MainWindow", u"x\u8f74/\u5217\u53f7", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"\u8d77\u59cb", None))
        self.xStartEdit.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"\u6b65\u957f", None))
        self.xStepEdit.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.yAxisGroup.setTitle(QCoreApplication.translate("MainWindow", u"y\u8f74/\u884c\u53f7", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"\u8d77\u59cb", None))
        self.yStartEdit.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"\u6b65\u957f", None))
        self.yStepEdit.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"\u74e6\u7247\u5c5e\u6027", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"\u9ad8\u5ea6", None))
        self.tileHeightLineEdit.setText("")
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"\u5bbd\u5ea6", None))
        self.tileWidthLineEdit.setText("")
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u74e6\u7247\u56fe\u6839\u76ee\u5f55\uff1a", None))
        self.tileDirEdit.setText("")
        self.browseTileDirBtn.setText(QCoreApplication.translate("MainWindow", u"\u6d4f\u89c8...", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"\u8fdb\u7a0b\u6570\uff1a", None))
        self.nProcEdit.setText(QCoreApplication.translate("MainWindow", u"8", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"\u4fdd\u5b58\u683c\u5f0f\uff1a", None))
        self.resultFormatComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u".png", None))
        self.resultFormatComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u".jpg", None))
        self.resultFormatComboBox.setItemText(2, QCoreApplication.translate("MainWindow", u".jpeg", None))
        self.resultFormatComboBox.setItemText(3, QCoreApplication.translate("MainWindow", u".tiff", None))
        self.resultFormatComboBox.setItemText(4, QCoreApplication.translate("MainWindow", u".tif", None))
        self.resultFormatComboBox.setItemText(5, QCoreApplication.translate("MainWindow", u".gif", None))

        self.processBtn.setText(QCoreApplication.translate("MainWindow", u"\u5f00\u59cb\u5904\u7406", None))
        self.imageLabel.setText(QCoreApplication.translate("MainWindow", u"\u8fdb\u5ea6\u5c55\u793a\u533a\u57df", None))
    # retranslateUi


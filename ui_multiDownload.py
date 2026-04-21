from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(600, 700)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setSpacing(10)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.param_group = QGroupBox(self.centralwidget)
        self.param_group.setObjectName(u"param_group")
        self.form_layout = QFormLayout(self.param_group)
        self.form_layout.setObjectName(u"form_layout")
        self.level_label = QLabel(self.param_group)
        self.level_label.setObjectName(u"level_label")

        self.form_layout.setWidget(1, QFormLayout.LabelRole, self.level_label)

        self.level_spin = QSpinBox(self.param_group)
        self.level_spin.setObjectName(u"level_spin")
        self.level_spin.setMinimum(1)
        self.level_spin.setMaximum(22)
        self.level_spin.setValue(16)

        self.form_layout.setWidget(1, QFormLayout.FieldRole, self.level_spin)

        self.lt_lat_label = QLabel(self.param_group)
        self.lt_lat_label.setObjectName(u"lt_lat_label")

        self.form_layout.setWidget(2, QFormLayout.LabelRole, self.lt_lat_label)

        self.lt_lat_spin = QDoubleSpinBox(self.param_group)
        self.lt_lat_spin.setObjectName(u"lt_lat_spin")
        self.lt_lat_spin.setDecimals(6)
        self.lt_lat_spin.setMinimum(-90.000000000000000)
        self.lt_lat_spin.setMaximum(90.000000000000000)
        self.lt_lat_spin.setValue(36.161000000000001)

        self.form_layout.setWidget(2, QFormLayout.FieldRole, self.lt_lat_spin)

        self.lt_lon_label = QLabel(self.param_group)
        self.lt_lon_label.setObjectName(u"lt_lon_label")

        self.form_layout.setWidget(3, QFormLayout.LabelRole, self.lt_lon_label)

        self.lt_lon_spin = QDoubleSpinBox(self.param_group)
        self.lt_lon_spin.setObjectName(u"lt_lon_spin")
        self.lt_lon_spin.setDecimals(6)
        self.lt_lon_spin.setMinimum(-180.000000000000000)
        self.lt_lon_spin.setMaximum(180.000000000000000)
        self.lt_lon_spin.setValue(103.553299999999993)

        self.form_layout.setWidget(3, QFormLayout.FieldRole, self.lt_lon_spin)

        self.rb_lat_label = QLabel(self.param_group)
        self.rb_lat_label.setObjectName(u"rb_lat_label")

        self.form_layout.setWidget(4, QFormLayout.LabelRole, self.rb_lat_label)

        self.rb_lat_spin = QDoubleSpinBox(self.param_group)
        self.rb_lat_spin.setObjectName(u"rb_lat_spin")
        self.rb_lat_spin.setDecimals(6)
        self.rb_lat_spin.setMinimum(-90.000000000000000)
        self.rb_lat_spin.setMaximum(90.000000000000000)
        self.rb_lat_spin.setValue(36.020299999999999)

        self.form_layout.setWidget(4, QFormLayout.FieldRole, self.rb_lat_spin)

        self.rb_lon_label = QLabel(self.param_group)
        self.rb_lon_label.setObjectName(u"rb_lon_label")

        self.form_layout.setWidget(5, QFormLayout.LabelRole, self.rb_lon_label)

        self.rb_lon_spin = QDoubleSpinBox(self.param_group)
        self.rb_lon_spin.setObjectName(u"rb_lon_spin")
        self.rb_lon_spin.setDecimals(6)
        self.rb_lon_spin.setMinimum(-180.000000000000000)
        self.rb_lon_spin.setMaximum(180.000000000000000)
        self.rb_lon_spin.setValue(103.955699999999993)

        self.form_layout.setWidget(5, QFormLayout.FieldRole, self.rb_lon_spin)

        self.path_label = QLabel(self.param_group)
        self.path_label.setObjectName(u"path_label")

        self.form_layout.setWidget(6, QFormLayout.LabelRole, self.path_label)

        self.path_layout = QHBoxLayout()
        self.path_layout.setObjectName(u"path_layout")
        self.path_edit = QLineEdit(self.param_group)
        self.path_edit.setObjectName(u"path_edit")

        self.path_layout.addWidget(self.path_edit)

        self.browse_btn = QPushButton(self.param_group)
        self.browse_btn.setObjectName(u"browse_btn")
        self.browse_btn.setMinimumSize(QSize(120, 0))
        self.browse_btn.setMaximumSize(QSize(120, 16777215))

        self.path_layout.addWidget(self.browse_btn)


        self.form_layout.setLayout(6, QFormLayout.FieldRole, self.path_layout)

        self.workers_label = QLabel(self.param_group)
        self.workers_label.setObjectName(u"workers_label")

        self.form_layout.setWidget(7, QFormLayout.LabelRole, self.workers_label)

        self.workers_spin = QSpinBox(self.param_group)
        self.workers_spin.setObjectName(u"workers_spin")
        self.workers_spin.setMinimum(1)
        self.workers_spin.setMaximum(4096)
        self.workers_spin.setValue(512)

        self.form_layout.setWidget(7, QFormLayout.FieldRole, self.workers_spin)

        self.source_comboBox = QComboBox(self.param_group)
        self.source_comboBox.addItem("")
        self.source_comboBox.addItem("")
        self.source_comboBox.addItem("")
        self.source_comboBox.addItem("")
        self.source_comboBox.setObjectName(u"source_comboBox")

        self.form_layout.setWidget(0, QFormLayout.FieldRole, self.source_comboBox)

        self.label = QLabel(self.param_group)
        self.label.setObjectName(u"label")

        self.form_layout.setWidget(0, QFormLayout.LabelRole, self.label)


        self.main_layout.addWidget(self.param_group)

        self.progress_group = QGroupBox(self.centralwidget)
        self.progress_group.setObjectName(u"progress_group")
        self.progress_layout = QVBoxLayout(self.progress_group)
        self.progress_layout.setObjectName(u"progress_layout")
        self.progress_bar = QProgressBar(self.progress_group)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(0)

        self.progress_layout.addWidget(self.progress_bar)


        self.main_layout.addWidget(self.progress_group)

        self.log_group = QGroupBox(self.centralwidget)
        self.log_group.setObjectName(u"log_group")
        self.log_layout = QVBoxLayout(self.log_group)
        self.log_layout.setObjectName(u"log_layout")
        self.log_text = QTextEdit(self.log_group)
        self.log_text.setObjectName(u"log_text")
        self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_text.setReadOnly(True)

        self.log_layout.addWidget(self.log_text)


        self.main_layout.addWidget(self.log_group)

        self.btn_layout = QHBoxLayout()
        self.btn_layout.setObjectName(u"btn_layout")
        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.btn_layout.addItem(self.horizontalSpacer)

        self.start_btn = QPushButton(self.centralwidget)
        self.start_btn.setObjectName(u"start_btn")
        self.start_btn.setMinimumSize(QSize(0, 34))

        self.btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton(self.centralwidget)
        self.stop_btn.setObjectName(u"stop_btn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumSize(QSize(0, 34))

        self.btn_layout.addWidget(self.stop_btn)

        self.open_dir_btn = QPushButton(self.centralwidget)
        self.open_dir_btn.setObjectName(u"open_dir_btn")
        self.open_dir_btn.setMinimumSize(QSize(0, 34))

        self.btn_layout.addWidget(self.open_dir_btn)

        self.clear_log_btn = QPushButton(self.centralwidget)
        self.clear_log_btn.setObjectName(u"clear_log_btn")
        self.clear_log_btn.setMinimumSize(QSize(0, 34))

        self.btn_layout.addWidget(self.clear_log_btn)


        self.main_layout.addLayout(self.btn_layout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        self.statusbar.setEnabled(True)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"\u5730\u56fe\u74e6\u7247\u4e0b\u8f7d\u5668", None))
        self.param_group.setTitle(QCoreApplication.translate("MainWindow", u"\u4e0b\u8f7d\u53c2\u6570", None))
        self.level_label.setText(QCoreApplication.translate("MainWindow", u"\u7f29\u653e\u7ea7\u522b (1-22):", None))
        self.lt_lat_label.setText(QCoreApplication.translate("MainWindow", u"\u5de6\u4e0a\u89d2\u7eac\u5ea6:", None))
        self.lt_lon_label.setText(QCoreApplication.translate("MainWindow", u"\u5de6\u4e0a\u89d2\u7ecf\u5ea6:", None))
        self.rb_lat_label.setText(QCoreApplication.translate("MainWindow", u"\u53f3\u4e0b\u89d2\u7eac\u5ea6:", None))
        self.rb_lon_label.setText(QCoreApplication.translate("MainWindow", u"\u53f3\u4e0b\u89d2\u7ecf\u5ea6:", None))
        self.path_label.setText(QCoreApplication.translate("MainWindow", u"\u4fdd\u5b58\u8def\u5f84:", None))
        self.path_edit.setText(QCoreApplication.translate("MainWindow", u"D:\\satellite\\", None))
        self.path_edit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"\u8bf7\u9009\u62e9\u74e6\u7247\u4fdd\u5b58\u76ee\u5f55...", None))
        self.browse_btn.setText(QCoreApplication.translate("MainWindow", u"\u6d4f\u89c8", None))
        self.workers_label.setText(QCoreApplication.translate("MainWindow", u"\u5e76\u53d1\u7ebf\u7a0b\u6570:", None))
        self.source_comboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"Google Earth", None))
        self.source_comboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"\u9ad8\u5fb7\u77e2\u91cf\u5e95\u56fe", None))
        self.source_comboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"\u9ad8\u5fb7\u536b\u661f\u5f71\u50cf", None))
        self.source_comboBox.setItemText(3, QCoreApplication.translate("MainWindow", u"\u9ad8\u5fb7\u8def\u7f51\u6807\u8bb0", None))

        self.label.setText(QCoreApplication.translate("MainWindow", u"\u6570\u636e\u6e90\uff1a", None))
        self.progress_group.setTitle(QCoreApplication.translate("MainWindow", u"\u4e0b\u8f7d\u8fdb\u5ea6", None))
        self.progress_bar.setFormat(QCoreApplication.translate("MainWindow", u"%p%  (%v / %m)", None))
        self.log_group.setTitle(QCoreApplication.translate("MainWindow", u"\u8fd0\u884c\u65e5\u5fd7", None))
        self.start_btn.setText(QCoreApplication.translate("MainWindow", u"\u25b6 \u5f00\u59cb\u4e0b\u8f7d", None))
        self.stop_btn.setText(QCoreApplication.translate("MainWindow", u"\u23f9 \u505c\u6b62\u4e0b\u8f7d", None))
        self.open_dir_btn.setText(QCoreApplication.translate("MainWindow", u"📂 打开目录", None))
        self.clear_log_btn.setText(QCoreApplication.translate("MainWindow", u"🗑 清空日志", None))
    # retranslateUi


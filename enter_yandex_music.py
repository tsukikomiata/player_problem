from PyQt5 import QtCore, QtGui, QtWidgets


class Yam_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(280, 170)
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(10, 10, 181, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(10, 50, 55, 22))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.login_yan = QtWidgets.QLineEdit(Dialog)
        self.login_yan.setGeometry(QtCore.QRect(80, 50, 191, 22))
        self.login_yan.setObjectName("login_yan")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(10, 90, 55, 22))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.pass_yan = QtWidgets.QLineEdit(Dialog)
        self.pass_yan.setGeometry(QtCore.QRect(80, 90, 191, 22))
        self.pass_yan.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pass_yan.setObjectName("pass_yan")
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(190, 130, 80, 30))
        self.pushButton.setObjectName("pushButton")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "Вход в Яндекс.Музыка"))
        self.label_2.setText(_translate("Dialog", "Логин"))
        self.label_3.setText(_translate("Dialog", "Пароль"))
        self.pushButton.setText(_translate("Dialog", "Войти"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Yam_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
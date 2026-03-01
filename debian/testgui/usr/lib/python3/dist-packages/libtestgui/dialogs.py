

from PyQt6.QtWidgets import QMessageBox


def warn_msg_ok(parent, msg, title=None):
	# dialogs.warn_msg_ok(parent, msg, 'title')
	msg_box = QMessageBox(parent)
	msg_box.setIcon(QMessageBox.Icon.Warning)
	msg_box.setWindowTitle(title)
	msg_box.setText(msg)
	msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
	msg_box.exec()


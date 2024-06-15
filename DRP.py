# DRP - A repository program for downloading operating systems.
# Copyright (C) 2024 Esther
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# Project Name: DRP
# Original Author: Esther
# License: GNU General Public License v3.0
#
# This code was originally created by Esther.
# If you modify this code, please keep this notice and mention the original author.

# DRP Copyright (C) 2024 Esther
# This program comes with ABSOLUTELY NO WARRANTY;
# This is free software, and you are welcome to redistribute it under certain conditions;

# For more information, contact: @onlysterbr Twitter (X)

import sys
import json
import urllib.request
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QComboBox, QMessageBox, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QProgressBar, QLineEdit, QTextEdit, QDialog, QScrollArea, QAction, QSpinBox  # Add QSpinBox import here
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSettings, QDir
from PyQt5.QtGui import QDesktopServices
from qtmodern.styles import dark
from qtmodern.windows import ModernWindow
from packaging.version import Version

class DownloadThread(QThread):
    # Sinais para atualizar a interface de usuário
    update_progress = pyqtSignal(int)
    update_speed = pyqtSignal(float, QProgressBar)
    update_buttons = pyqtSignal(bool, bool)  # Para atualizar os estados dos botões
    cancel_download = pyqtSignal()  # Novo sinal para cancelamento de download

    def __init__(self, url, save_path, progress_bar, parent=None):
        super().__init__(parent)
        self.url = url
        self.save_path = save_path
        self.progress_bar = progress_bar
        self.start_time = None
        self.downloaded_bytes = 0
        self.paused = False  # Flag para controle de pausa
        self._terminate = False

    def run(self):
        try:
            self.start_time = time.time()
            self.request, _ = urllib.request.urlretrieve(self.url, self.save_path, reporthook=self.report_hook)
        except Exception as e:
            if self._terminate:
                self.update_progress_cancel()
            else:
                print(f"Download error: {e}")

    def report_hook(self, blocknum, blocksize, totalsize):
        if self._terminate:
            raise Exception("Download cancelled by user.")

        if self.paused:
            while self.paused:
                time.sleep(1)

        if totalsize > 0:
            self.downloaded_bytes += blocksize
            progress = blocknum * blocksize * 100 / totalsize
            self.update_progress.emit(int(progress))
            
            elapsed_time = time.time() - self.start_time
            download_speed = (self.downloaded_bytes / 1024 / 1024) / elapsed_time if elapsed_time > 0 else 0
            self.update_speed.emit(download_speed, self.progress_bar)

    def toggle_pause(self):
        self.paused = not self.paused
        self.update_buttons.emit(not self.paused, self.paused)

    def terminate(self):
        self._terminate = True
        urllib.request.urlcleanup()

    def update_progress_cancel(self):
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        self.progress_bar.setAlignment(Qt.AlignCenter)  # Centralizar texto

    def restore_progress_bar(self):
        self.progress_bar.setStyleSheet("")  # Remover estilo para voltar ao padrão
        self.progress_bar.setAlignment(Qt.AlignLeft)  # Alinhar texto à esquerda padrão

class LicenseDialog(QDialog):
    def __init__(self, license_text, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle('License')

        layout = QVBoxLayout(self)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)
        text_edit.setPlainText(license_text)

        scroll_area.setWidget(text_edit)

        layout.addWidget(scroll_area)

        self.setMinimumWidth(600)  # Definindo a largura mínima da janela

        self.setLayout(layout)
            
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings_file = 'config.json'  # Nome do arquivo de configuração JSON
        self.settings = QSettings("DRP Studios", "DRP")

        self.settings_file = 'config.json'  # Nome do arquivo de configuração JSON
        self.download_path = ''  # Inicialização da variável para o caminho de download
        self.download_path_edit = QLineEdit() 

        self.limit_speed_spinbox = QSpinBox()

        self.load_settings()

        self.setWindowTitle('DRP 1.1 - Pride')
        self.setGeometry(200, 200, 600, 400)

        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.official_os_tab = self.create_os_tab('https://raw.githubusercontent.com/SterTheStar/DRPBR/main/repositorio.json', 'Official OS')
        self.mod_os_tab = self.create_os_tab('https://raw.githubusercontent.com/SterTheStar/DRPBR/main/modosrepositorio.json', 'Mod OS')
        self.settings_tab = self.create_settings_tab()

        self.tab_widget.addTab(self.official_os_tab, 'Official OS')
        self.tab_widget.addTab(self.mod_os_tab, 'Mod OS')
        self.tab_widget.addTab(self.settings_tab, 'Settings')

        QTimer.singleShot(100, self.check_update_and_display_changelog)

        self.download_thread = None

        self.setStyleSheet('')

        self.load_settings_theme()

    def check_update_and_display_changelog(self):
        url = 'https://raw.githubusercontent.com/SterTheStar/DRPBR/main/changelogs.json'

        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode()
                changelogs = json.loads(content)

                latest_version = max(changelogs.keys(), key=lambda v: Version(v))

                if Version('1.1') < Version(latest_version):
                    # Build the changelog text
                    changelog_text = f"Version: {changelogs[latest_version]['version']}\n"
                    changelog_text += f"Date: {changelogs[latest_version]['date']}\n\n"
                    changelog_text += "Changes:\n"
                    for change in changelogs[latest_version]['changes']:
                        changelog_text += f"- {change}\n"

                    # Check if update is needed
                    if Version('1.1') < Version(latest_version):
                        # Ask user if they want to update and show changelog
                        reply = QMessageBox.question(self, 'Update Available',
                                                     f"A new version ({latest_version}) is available.\n\n"
                                                     f"Do you want to update and view changelog?\n\n"
                                                     f"{changelog_text}",
                                                     QMessageBox.Yes | QMessageBox.No)

                        if reply == QMessageBox.Yes:
                            # Proceed with update if user agrees
                            update_link = changelogs[latest_version].get('update_link')
                            if update_link:
                                QDesktopServices.openUrl(QUrl(update_link))
                        else:
                            return
                    else:
                        # Version is up to date, show only changelog
                        QMessageBox.information(self, 'Changelog',
                                                f"Version: {changelogs[latest_version]['version']}\n"
                                                f"Date: {changelogs[latest_version]['date']}\n\n"
                                            f"Changes:\n"
                                            f"{changelog_text}")
                else:
                    # No update available, inform the user
                    QMessageBox.information(self, 'Up to Date', 'You are already using the latest version.')

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to perform update or load changelog: {e}')

    def load_settings(self):
        self.settings.beginGroup("DownloadSettings")
        self.download_path = self.settings.value("download_path", "")
        self.download_speed = self.settings.value("download_speed", 0)
        self.settings.endGroup()

        try:
            with open(self.settings_file, 'r') as f:
                json_data = json.load(f)
                self.download_path = json_data.get('download_path', '')
                self.download_speed = json_data.get('download_speed', 0)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Failed to load settings from JSON: {e}")

        # Update QLineEdit only if it is initialized
        if self.download_path_edit:
            self.download_path_edit.setText(self.download_path)  # Check before setting text

        self.limit_speed_spinbox.setValue(int(self.download_speed))

    def save_settings(self):
        self.settings.beginGroup("DownloadSettings")
        self.settings.setValue("download_path", self.download_path)
        self.settings.setValue("download_speed", self.limit_speed_spinbox.value())  # Salvando o valor do spinbox
        self.settings.endGroup()

        self.save_settings_to_json()

    def save_settings_to_json(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump({'download_path': self.download_path, 'download_speed': self.limit_speed_spinbox.value()}, f, indent=4)
        except Exception as e:
            print(f"Failed to save settings to JSON: {e}")

    def create_os_tab(self, json_url, tab_name):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        title_label = QLabel(f'DRP {tab_name}', tab)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Courier New', 25))
        layout.addWidget(title_label)

        combo_layout1 = QHBoxLayout()
        layout.addLayout(combo_layout1)

        select_os_label = QLabel('Select OS:', tab)
        select_os_label.setAlignment(Qt.AlignLeft)
        combo_layout1.addWidget(select_os_label)

        combo_windows = QComboBox(tab)
        combo_layout1.addWidget(combo_windows)

        combo_layout2 = QHBoxLayout()
        layout.addLayout(combo_layout2)

        select_arch_label = QLabel('Select Architecture:', tab)
        select_arch_label.setAlignment(Qt.AlignLeft)
        combo_layout2.addWidget(select_arch_label)

        combo_arch = QComboBox(tab)
        combo_layout2.addWidget(combo_arch)

        combo_layout3 = QHBoxLayout()
        layout.addLayout(combo_layout3)

        select_version_label = QLabel('Select Version:', tab)
        select_version_label.setAlignment(Qt.AlignLeft)
        combo_layout3.addWidget(select_version_label)

        combo_version = QComboBox(tab)
        combo_layout3.addWidget(combo_version)

        # Layout horizontal para os botões
        button_layout = QHBoxLayout()

        btn_download = QPushButton('Download', tab)
        button_layout.addWidget(btn_download)

        btn_pause_resume = QPushButton('Pause', tab)  # Adicionando botão de pausa
        button_layout.addWidget(btn_pause_resume)
        btn_pause_resume.setEnabled(False)

        btn_cancel = QPushButton('Cancel', tab)
        btn_cancel.setEnabled(False)
        button_layout.addWidget(btn_cancel)

        btn_cancel.clicked.connect(self.cancel_download)

        layout.addLayout(button_layout)  # Adiciona o layout dos botões ao layout principal

        progress_bar = QProgressBar(tab)
        layout.addWidget(progress_bar)

        try:
            download_data = self.load_data_from_json(json_url)
            combo_windows.addItems([entry['windows_version'] for entry in download_data])
            
            # Configuração inicial dos combos
            if download_data:
                self.on_windows_version_changed(combo_windows, combo_arch, combo_version, download_data)
                combo_windows.setCurrentIndex(0)  # Define o primeiro item como selecionado inicialmente

        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load JSON data: {e}')

        combo_windows.currentIndexChanged.connect(lambda: self.on_windows_version_changed(combo_windows, combo_arch, combo_version, download_data))
        combo_arch.currentIndexChanged.connect(lambda: self.on_architecture_changed(combo_windows, combo_arch, combo_version, download_data))
        btn_download.clicked.connect(lambda: self.download_iso(combo_windows, combo_arch, combo_version, download_data, progress_bar, btn_cancel, btn_pause_resume))
        btn_cancel.clicked.connect(self.cancel_download)

        # Novo layout para a configuração de download

        button_layout2 = QHBoxLayout()
        btn_open_browser = QPushButton('Download in WebBrowser', tab)
        button_layout2.addWidget(btn_open_browser)
        layout.addLayout(button_layout2)

        btn_open_browser.clicked.connect(lambda: self.open_in_browser(combo_windows, combo_arch, combo_version, download_data))
        btn_pause_resume.clicked.connect(lambda: self.pause_resume_download(btn_pause_resume, btn_cancel))

        return tab

    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        settings_layout = QHBoxLayout()

        download_path_label = QLabel('Download Path:', tab)
        settings_layout.addWidget(download_path_label)

        self.download_path_edit = QLineEdit()
        settings_layout.addWidget(self.download_path_edit)

        btn_choose_path = QPushButton('🔎', tab)
        settings_layout.addWidget(btn_choose_path)

        layout.addLayout(settings_layout)

        # Adicionando a opção de limite de velocidade de download
        limit_speed_layout = QHBoxLayout()

        limit_speed_label = QLabel('Download Speed Limit (MB/s): (In Working)', tab)
        limit_speed_layout.addWidget(limit_speed_label)

        self.limit_speed_spinbox = QSpinBox(tab)
        self.limit_speed_spinbox.setMinimum(0)  # Definindo valor mínimo como 0 MB/s
        self.limit_speed_spinbox.setMaximum(100)  # Definindo valor máximo como 100 MB/s
        limit_speed_layout.addWidget(self.limit_speed_spinbox)

        layout.addLayout(limit_speed_layout)

        # Dentro da função create_settings_tab()

        theme_layout = QHBoxLayout()
        layout.addLayout(theme_layout)

        # Dropdown para escolher o estilo da janela principal
        style_label = QLabel('Select Main Window Style:', tab)
        theme_layout.addWidget(style_label)

        self.style_dropdown = QComboBox(tab)
        self.style_dropdown.addItems(['Default Style', 'Dark Style', 'Pride Style'])  # Exemplo de opções
        theme_layout.addWidget(self.style_dropdown)

        # Conectar sinal para mudar o estilo da janela principal
        self.style_dropdown.currentIndexChanged.connect(self.change_main_window_style)

        # Adicionando espaçamento flexível para empurrar os botões para a parte inferior
        layout.addStretch()

        # Nova linha para os botões na parte inferior alinhados à esquerda
        bottom_layout = QHBoxLayout()

        btn_source_code = QPushButton('Source Code', tab)
        btn_source_code.setMinimumWidth(100)  # Definindo largura mínima
        bottom_layout.addWidget(btn_source_code)

        btn_creator = QPushButton('Creator', tab)
        btn_creator.setMinimumWidth(100)  # Definindo largura mínima
        bottom_layout.addWidget(btn_creator)

        btn_license = QPushButton('License', tab)
        btn_license.setMinimumWidth(100)  # Definindo largura mínima
        bottom_layout.addWidget(btn_license)

        layout.addLayout(bottom_layout)

        # Adicionando o botão "Save Settings" em uma linha separada abaixo dos botões acima
        layout.addSpacing(0)  # Espaçamento entre as linhas
        btn_save_settings = QPushButton('Save Settings', tab)
        layout.addWidget(btn_save_settings, alignment=Qt.AlignRight)  # Alinhando à esquerda

        # Conectando os sinais aos slots (eventos)
        btn_source_code.clicked.connect(self.open_source_code)
        btn_creator.clicked.connect(self.open_creator)
        btn_choose_path.clicked.connect(self.choose_download_path)
        btn_save_settings.clicked.connect(self.save_settings)
        btn_license.clicked.connect(self.show_license)

        # Carregando configurações
        self.load_settings()

        return tab
    
    def change_main_window_style(self):
        selected_style = self.style_dropdown.currentText()
        file_path = ''

        if selected_style == 'Dark Style':
            file_path = 'data/style_dark.css'
        elif selected_style == 'Pride Style':
            file_path = 'data/style_trans.css'
        else:
            file_path = 'data/style.css'

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                style = f.read()
                self.setStyleSheet(style)
                self.settings.setValue("main_window_style", selected_style)
        except FileNotFoundError:
            print(f"Error: Could not find the style file '{file_path}'")
            # Handle the error as per your application's requirements
        except Exception as e:
            print(f"Error: {e}")
            # Handle other potential exceptions

    def save_style_settings(self, selected_style):
        self.settings.setValue("main_window_style", selected_style)
        self.settings.sync()  # Garante que as alterações sejam salvas imediatamente

    def load_settings_theme(self):
        saved_style = self.settings.value("main_window_style")

        if saved_style is not None and self.style_dropdown is not None:
            index = self.style_dropdown.findText(saved_style)
            if index != -1:
                self.style_dropdown.setCurrentIndex(index)
            else:
                self.apply_default_style()
        else:
            self.apply_default_style()


    def apply_default_style(self):
        # Carrega o estilo padrão
        with open(self.default_style_path, 'r', encoding='utf-8') as f:
            self.setStyleSheet(f.read())
    
    def show_license(self):
        try:
            with open('license.json', 'r', encoding='utf-8') as f:
                license_text = f.read()

                license_dialog = LicenseDialog(license_text, self)
                license_dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load license: {e}')
    
    def open_source_code(self):
        QDesktopServices.openUrl(QUrl('https://github.com/SterTheStar/DRPBR/'))

    def open_creator(self):
        QDesktopServices.openUrl(QUrl('https://github.com/SterTheStar'))

    def choose_download_path(self):
        download_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if download_path:
            self.download_path = download_path
            self.download_path_edit.setText(download_path)
            self.save_settings()

    def on_windows_version_changed(self, combo_windows, combo_arch, combo_version, download_data):
        selected_index = combo_windows.currentIndex()
        combo_arch.clear()
        combo_version.clear()

        if selected_index >= 0 and selected_index < len(download_data):
            versions = download_data[selected_index]['editions']
            combo_arch.addItems([version['architecture'] for version in versions])

            if versions:
                self.on_architecture_changed(combo_windows, combo_arch, combo_version, download_data)

    def on_architecture_changed(self, combo_windows, combo_arch, combo_version, download_data):
        selected_index = combo_windows.currentIndex()
        selected_architecture = combo_arch.currentText()
        combo_version.clear()

        if selected_index >= 0 and selected_index < len(download_data):
            versions = download_data[selected_index]['editions']
            for version in versions:
                if version['architecture'] == selected_architecture:
                    combo_version.addItems(version['versions'].keys())

    def cancel_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()

    def download_iso(self, combo_windows, combo_arch, combo_version, download_data, progress_bar, btn_cancel, btn_pause_resume):
        selected_index = combo_windows.currentIndex()
        selected_architecture = combo_arch.currentText()
        selected_version = combo_version.currentText()
        btn_pause_resume.setEnabled(True)

        btn_download = self.sender()
        btn_download.setEnabled(False)
        btn_cancel.setEnabled(True)

        if selected_index >= 0 and selected_index < len(download_data):
            versions = download_data[selected_index]['editions']
            for version in versions:
                if version['architecture'] == selected_architecture:
                    if selected_version in version['versions']:
                        download_url = version['versions'][selected_version]
                       # Construindo o caminho e nome do arquivo
                        filename = f"DRP_{combo_windows.currentText()}_{selected_architecture}_{selected_version}.iso"
                        save_path = f"{self.download_path}/{filename}"
                        speed_limit = self.limit_speed_spinbox.value() * 1024 * 1024  # Convertendo para bytes/s

                        # Cancelar download anterior, se houver
                        if self.download_thread and self.download_thread.isRunning():
                            self.cancel_download()

                        # Criar novo thread de download
                        self.download_thread = DownloadThread(download_url, save_path, progress_bar)
                        self.download_thread.update_progress.connect(progress_bar.setValue)
                        self.download_thread.update_speed.connect(self.update_download_speed)
                        self.download_thread.cancel_download.connect(self.update_progress_cancel)  # Conexão para atualizar quando cancelado
                        self.download_thread.start()
                        self.download_thread.finished.connect(lambda: self.on_download_finished(btn_cancel, btn_download, btn_pause_resume))
                        return
        else:
            QMessageBox.warning(self, 'Selection Error', 'Failed to find a download link for selected OS and version.')

    def update_progress_cancel(self):
        if self.download_thread:
            self.download_thread.update_progress_cancel()

    def update_button_state(self, btn_pause_resume, btn_cancel, enable_pause, enable_cancel):
        btn_pause_resume.setEnabled(enable_pause)
        btn_cancel.setEnabled(enable_cancel)

    def pause_resume_download(self, btn_pause_resume, btn_cancel):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.toggle_pause()
            if self.download_thread.paused:
                btn_pause_resume.setText('Resume')
                btn_cancel.setEnabled(False)
            else:
                btn_pause_resume.setText('Pause')
                btn_cancel.setEnabled(True)

    def update_download_speed(self, speed, progress_bar):
        current_progress = progress_bar.value()
        if current_progress < 100:
            progress_bar.setFormat(f"Downloading... {current_progress}% - Speed: {speed:.2f} MB/s")
        else:
            progress_bar.setFormat(f"Completed.")

    def on_download_finished(self, btn_cancel, btn_download, btn_pause_resume):
        btn_cancel.setEnabled(False)
        btn_pause_resume.setEnabled(False)
        btn_download.setEnabled(True)

        if self.download_thread and self.download_thread.isFinished():
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Notification")
            msg_box.setText("Download Finished.")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowFlags(Qt.FramelessWindowHint)

            # Estilo CSS para remover a borda onde fica o botão de fechar
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #1e1e1e;
                    border: none; /* Remove a borda */
                }
                QMessageBox QLabel {
                    color: #dcdcdc;
                }
                QMessageBox QPushButton {
                    background-color: #007bff;
                    color: white;
                    padding: 5px;
                    border-radius: 5px;
                    min-width: 80px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #0056b3;
                }
            """)

            # Adicionando botão OK personalizado
            ok_button = msg_box.addButton("OK", QMessageBox.AcceptRole)
            ok_button.setStyleSheet("background-color: #28a745; color: white; padding: 5px; border-radius: 5px; min-width: 80px;")
            ok_button.clicked.connect(msg_box.accept)

            msg_box.exec_()

    def cancel_download(self):
        if self.download_thread:
            if self.download_thread.isRunning():
                self.download_thread.terminate()
                self.download_thread.wait()

    def open_in_browser(self, combo_windows, combo_arch, combo_version, download_data):
        selected_index = combo_windows.currentIndex()
        selected_architecture = combo_arch.currentText()
        selected_version = combo_version.currentText()

        if selected_index >= 0 and selected_index < len(download_data):
            versions = download_data[selected_index]['editions']
            for version in versions:
                if version['architecture'] == selected_architecture:
                    if selected_version in version['versions']:
                        download_url = version['versions'][selected_version]
                        QDesktopServices.openUrl(QUrl(download_url))

    def load_data_from_json(self, url):
        try:
            with urllib.request.urlopen(url) as response:
                data = response.read().decode()
                return json.loads(data)
        except Exception as e:
            raise Exception(f"Failed to load JSON data from {url}: {e}")

def main():
    app = QApplication(sys.argv)
    dark(app)
    window = ModernWindow(MainWindow())
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

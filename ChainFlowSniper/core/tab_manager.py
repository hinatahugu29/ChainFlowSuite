import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTabBar, QPushButton, QHBoxLayout
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtCore import Qt, Signal, QUrl
from core.browser import SniperBrowser

class SniperTabManager(QWidget):
    tab_changed = Signal(object) # current browser
    title_changed = Signal(str)
    url_changed = Signal(QUrl)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # Add New Tab Button
        self.add_button = QPushButton("+")
        self.add_button.setFixedSize(30, 25)
        self.add_button.clicked.connect(lambda: self.add_tab())
        self.tabs.setCornerWidget(self.add_button, Qt.TopLeftCorner)

        self.layout.addWidget(self.tabs)

    def add_tab(self, url=None, label="New Tab"):
        browser = SniperBrowser()
        # SniperBrowser.createWindow allows it to handle link requests by opening a new tab
        browser.set_tab_manager(self) 
        
        page = QWebEnginePage(self.main_window.profile, browser)
        browser.setPage(page)
        
        # Setup Channel for this specific page
        browser.page().setWebChannel(self.main_window.channel)
        
        index = self.tabs.addTab(browser, label)
        
        # Connect signals
        browser.urlChanged.connect(lambda qurl: self.on_browser_url_changed(browser, qurl))
        browser.titleChanged.connect(lambda title: self.on_browser_title_changed(browser, title))
        
        self.tabs.setCurrentIndex(index)
        
        if url:
            browser.setUrl(QUrl(url))
        else:
            browser.setUrl(QUrl("https://www.google.com"))
            
        return browser

    def close_tab(self, index):
        if self.tabs.count() > 1:
            browser = self.tabs.widget(index)
            self.tabs.removeTab(index)
            browser.deleteLater()

    def on_tab_changed(self, index):
        browser = self.tabs.widget(index)
        if browser:
            self.tab_changed.emit(browser)
            self.url_changed.emit(browser.url())
            self.title_changed.emit(browser.title())

    def on_browser_url_changed(self, browser, qurl):
        if browser == self.current_browser():
            self.url_changed.emit(qurl)

    def on_browser_title_changed(self, browser, title):
        index = self.tabs.indexOf(browser)
        if index != -1:
            short_title = title[:15] + "..." if len(title) > 15 else title
            self.tabs.setTabText(index, short_title)
            self.tabs.setTabToolTip(index, title)
        
        if browser == self.current_browser():
            self.title_changed.emit(title)

    def current_browser(self):
        return self.tabs.currentWidget()

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import QTimer, QPropertyAnimation, QRect, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class NotificationWidget(QWidget):
    """Self-disposable notification popup that appears in the corner"""
    
    closed = pyqtSignal()
    
    def __init__(self, message, title="Уведомление", duration=3000, notification_type="info", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Ensure duration is an integer
        self.duration = int(duration) if duration is not None else 3000
        self.notification_type = notification_type
        
        self.setup_ui(title, message)
        self.setup_timer()
        self.setup_animation()
        
    def setup_ui(self, title, message):
        """Setup the notification UI"""
        self.setFixedSize(300, 100)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.close_notification)
        
        # Header layout with title and close button
        header_layout = QHBoxLayout()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        layout.addWidget(message_label)
        layout.addStretch()
        
        # Style based on notification type
        self.apply_style()
        
    def apply_style(self):
        """Apply styling based on notification type"""
        # Определяем цвета в зависимости от типа и темы
        # Проверяем, есть ли доступ к главному окну для определения темы
        dark_theme = False
        try:
            # Пытаемся получить доступ к главному окну через parent chain
            widget = self.parent()
            while widget and not hasattr(widget, 'dark_theme'):
                widget = widget.parent()
            if widget and hasattr(widget, 'dark_theme'):
                dark_theme = widget.dark_theme
        except:
            pass
        
        if self.notification_type == "error":
            if dark_theme:
                bg_color = "#4a1a1a"
                border_color = "#ff6b6b"
                text_color = "#ff9999"
            else:
                bg_color = "#ffebee"
                border_color = "#f44336"
                text_color = "#c62828"
        elif self.notification_type == "warning":
            if dark_theme:
                bg_color = "#4a3a1a"
                border_color = "#ffb74d"
                text_color = "#ffcc80"
            else:
                bg_color = "#fff3e0"
                border_color = "#ff9800"
                text_color = "#ef6c00"
        elif self.notification_type == "success":
            if dark_theme:
                bg_color = "#1a4a1a"
                border_color = "#66bb6a"
                text_color = "#a5d6a7"
            else:
                bg_color = "#e8f5e8"
                border_color = "#4caf50"
                text_color = "#2e7d32"
        else:  # info
            if dark_theme:
                bg_color = "#1a3a4a"
                border_color = "#42a5f5"
                text_color = "#90caf9"
            else:
                bg_color = "#e3f2fd"
                border_color = "#2196f3"
                text_color = "#1565c0"
            
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                color: {text_color};
            }}
            QPushButton {{
                background-color: transparent;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 10px;
            }}
        """)
        
    def setup_timer(self):
        """Setup auto-close timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.close_notification)
        if self.duration > 0:
            self.timer.start(self.duration)
            
    def setup_animation(self):
        """Setup slide-in animation"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        
    def show_notification(self, parent_widget=None):
        """Show the notification with slide-in animation"""
        if parent_widget:
            # Position in top-right corner of parent
            parent_rect = parent_widget.geometry()
            x = parent_rect.right() - self.width() - 20
            y = parent_rect.top() + 50
        else:
            # Position in top-right corner of screen
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.desktop().screenGeometry()
            x = screen.width() - self.width() - 20
            y = 50
            
        # Start position (off-screen)
        start_rect = QRect(x + self.width(), y, self.width(), self.height())
        end_rect = QRect(x, y, self.width(), self.height())
        
        self.setGeometry(start_rect)
        self.show()
        
        # Animate slide-in
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()
        
    def close_notification(self):
        """Close the notification with slide-out animation"""
        if self.timer.isActive():
            self.timer.stop()
            
        # Animate slide-out
        current_rect = self.geometry()
        end_rect = QRect(current_rect.right(), current_rect.y(), 
                        current_rect.width(), current_rect.height())
        
        self.animation.setStartValue(current_rect)
        self.animation.setEndValue(end_rect)
        self.animation.finished.connect(self.hide)
        self.animation.finished.connect(self.closed.emit)
        self.animation.start()
        
    def mousePressEvent(self, event):
        """Close on click"""
        self.close_notification()
        
class NotificationManager:
    """Manages multiple notifications to prevent overlap"""
    
    def __init__(self):
        self.notifications = []
        self.y_offset = 50
        
    def show_notification(self, message, title="Уведомление", duration=3000, 
                         notification_type="info", parent_widget=None):
        """Show a new notification"""
        notification = NotificationWidget(message, title, duration, notification_type, parent_widget)
        notification.closed.connect(lambda: self.remove_notification(notification))
        
        # Calculate position
        if parent_widget:
            parent_rect = parent_widget.geometry()
            x = parent_rect.right() - notification.width() - 20
            y = parent_rect.top() + self.y_offset
        else:
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.desktop().screenGeometry()
            x = screen.width() - notification.width() - 20
            y = self.y_offset
            
        # Adjust y position based on existing notifications
        for existing in self.notifications:
            if existing.isVisible():
                y += existing.height() + 10
                
        notification.setGeometry(x + notification.width(), y, 
                               notification.width(), notification.height())
        notification.show()
        
        # Animate slide-in
        end_rect = QRect(x, y, notification.width(), notification.height())
        notification.animation.setStartValue(notification.geometry())
        notification.animation.setEndValue(end_rect)
        notification.animation.start()
        
        self.notifications.append(notification)
        return notification
        
    def remove_notification(self, notification):
        """Remove notification from list"""
        if notification in self.notifications:
            self.notifications.remove(notification)
            notification.deleteLater()
            
    def clear_all(self):
        """Clear all notifications"""
        for notification in self.notifications[:]:
            notification.close_notification()
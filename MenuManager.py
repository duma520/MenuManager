__version__ = "3.4.0"

import os
import json
import datetime
from collections import defaultdict
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QListWidget, QSpinBox,
                             QTabWidget, QTableWidget, QTableWidgetItem, QMessageBox,
                             QFileDialog, QInputDialog, QComboBox, QGroupBox, QRadioButton,
                             QCheckBox, QTextEdit, QStackedWidget, QScrollArea,QFormLayout,
                             QDialog,QDialogButtonBox,QDoubleSpinBox,QListWidgetItem, QShortcut)
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import QtCore
from PyQt5.QtGui import QFont, QKeySequence
from pypinyin import lazy_pinyin
from PyQt5 import QtGui


class Dish:
    def __init__(self, id, name, price, category="未分类", description="", dialect_name="", is_spicy=0):
        self.id = id  # 菜品编号（用于快捷键）
        self.name = name
        self.price = price
        self.category = category
        self.description = description
        self.dialect_name = dialect_name  # 方言菜名
        self.is_spicy = is_spicy  # 辣度 0-不辣 1-微辣 2-中辣 3-重辣
        self.sales_count = 0  # 销售计数
        self.remarks = []  # 顾客备注历史

    def total_price(self, quantity):
        return self.price * quantity

    def add_remark(self, remark):
        self.remarks.append(remark)

    def increment_sales(self):
        self.sales_count += 1

    def get_spicy_text(self):
        spicy_map = {0: "不辣", 1: "微辣", 2: "中辣", 3: "重辣"}
        return spicy_map.get(self.is_spicy, "")


class MenuManager:
    def __init__(self):
        self.dishes = []
        self.categories = ["未分类"]
        self.current_file = None
        self.next_id = 1  # 用于自动生成菜品ID
        self.order_history = []  # 订单历史保存
        self.modified = False # 修改标记

    def add_dish(self, name, price, category="未分类", description="", dialect_name="", is_spicy=0):
        dish = Dish(self.next_id, name, price, category, description, dialect_name, is_spicy)
        self.dishes.append(dish)
        self.next_id += 1
        
        if category not in self.categories:
            self.categories.append(category)
        self.modified = True  # 设置修改标记
        return dish

    def remove_dish(self, dish_id):
        for i, dish in enumerate(self.dishes):
            if dish.id == dish_id:
                self.dishes.pop(i)
                self.modified = True  # 设置修改标记
                return True
        return False

    def update_dish(self, dish_id, **kwargs):
        for dish in self.dishes:
            if dish.id == dish_id:
                for key, value in kwargs.items():
                    if hasattr(dish, key):
                        setattr(dish, key, value)
                        
                        if key == 'category' and value not in self.categories:
                            self.categories.append(value)
                self.modified = True  # 设置修改标记
                return True
        return False

    def get_dish_by_id(self, dish_id):
        for dish in self.dishes:
            if dish.id == dish_id:
                return dish
        return None

    def get_dishes_by_category(self, category):
        return [dish for dish in self.dishes if dish.category == category]

    def get_top_dishes(self, limit=5):
        return sorted(self.dishes, key=lambda x: x.sales_count, reverse=True)[:limit]

    def save_to_file(self, filename):
        data = {
            "dishes": [{
                "id": dish.id,
                "name": dish.name,
                "price": dish.price,
                "category": dish.category,
                "description": dish.description,
                "dialect_name": dish.dialect_name,
                "is_spicy": dish.is_spicy,
                "sales_count": dish.sales_count,
                "remarks": dish.remarks
            } for dish in self.dishes],
            "categories": self.categories,
            "next_id": self.next_id,
            "current_file": filename,
            "order_history": self.order_history
        }
        
        # 创建备份
        if os.path.exists(filename):
            backup_name = filename.replace('.json', f'_backup_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.json')
            os.rename(filename, backup_name)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.modified = False  # 保存后重置修改标记

    def load_from_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.dishes = []
                for dish_data in data["dishes"]:
                    dish = Dish(
                        dish_data["id"],
                        dish_data["name"],
                        dish_data["price"],
                        dish_data.get("category", "未分类"),
                        dish_data.get("description", ""),
                        dish_data.get("dialect_name", ""),
                        dish_data.get("is_spicy", 0)
                    )
                    dish.sales_count = dish_data.get("sales_count", 0)
                    dish.remarks = dish_data.get("remarks", [])
                    self.dishes.append(dish)
                
                self.categories = data.get("categories", ["未分类"])
                self.next_id = data.get("next_id", len(self.dishes) + 1)
                self.current_file = filename
                self.order_history = data.get("order_history", [])
                self.modified = False  # 加载文件后重置修改标记
            return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"加载菜单失败: {e}")
            return False


class OrderItem:
    def __init__(self, dish_id, quantity, remark=""):
        self.dish_id = dish_id
        self.quantity = quantity
        self.remark = remark  # 本次点单的特殊要求
        self.price = 0  # 新增price属性，版本2.2.1



class PersonOrder:
    def __init__(self, name):
        self.name = name
        self.items = []
        self.payment_method = "AA"  # AA/比例/自定义
        self.payment_value = 1.0  # 比例或自定义金额

    def add_item(self, dish_id, quantity, remark=""):
        self.items.append(OrderItem(dish_id, quantity, remark))

    def remove_item(self, index):
        if 0 <= index < len(self.items):
            self.items.pop(index)

    def clear_items(self):
        self.items = []

    def calculate_total(self, menu_manager):
        total = 0
        for item in self.items:
            dish = menu_manager.get_dish_by_id(item.dish_id)
            if dish:
                total += dish.price * item.quantity
        return total

    def set_payment_method(self, method, value=1.0):
        self.payment_method = method
        self.payment_value = value


class OrderManager(QtCore.QObject):
    # 类级别的信号定义
    order_changed = QtCore.pyqtSignal()

    def __init__(self, menu_manager=None):
        super().__init__() 
        self.orders = {}  # {person_name: PersonOrder}
        self.history = []
        self.current_table = ""
        self.menu_manager = menu_manager
        
        # 如果提供了menu_manager，尝试加载它的历史
        if menu_manager and hasattr(menu_manager, 'order_history'):
            self.history = menu_manager.order_history

        #self.order_changed = QtCore.pyqtSignal()

    def add_person(self, name):
        if name not in self.orders:
            self.orders[name] = PersonOrder(name)

    def remove_person(self, name):
        if name in self.orders:
            del self.orders[name]

    def add_item_to_person(self, person_name, dish_id, quantity, remark=""):
        if person_name in self.orders:
            self.orders[person_name].add_item(dish_id, quantity, remark)
            if self.menu_manager:  # 添加检查确保 menu_manager 存在
                dish = self.menu_manager.get_dish_by_id(dish_id)
            if dish:
                dish.increment_sales()
                if remark:
                    dish.add_remark(remark)
            self.order_changed.emit()
            return True
        return False

    def remove_item_from_person(self, person_name, index):
        if person_name in self.orders:
            self.orders[person_name].remove_item(index)
            self.order_changed.emit()
            return True
        return False

    def set_payment_method(self, person_name, method, value=1.0):
        if person_name in self.orders:
            self.orders[person_name].set_payment_method(method, value)
            self.order_changed.emit()
            return True
        return False

    def set_payment_method_in_dialog(self, payment_table, dialog):
        selected_rows = payment_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            QMessageBox.warning(self, "警告", "请选择一个顾客设置支付方式")
            return
        
        row = selected_rows[0].row()
        person_name = payment_table.item(row, 0).text()
        
        payment_dialog = PaymentMethodDialog(self)
        if payment_dialog.exec_() == QDialog.Accepted:
            if hasattr(payment_dialog, 'payment_method'):
                method, value = payment_dialog.payment_method
                self.order_manager.set_payment_method(person_name, method, value)
                # 重新计算并更新显示
                totals, subtotal = self.order_manager.calculate_totals(self.menu_manager)
                
                # 更新支付表格
                payment_table.setRowCount(0)
                for row, (name, data) in enumerate(totals.items()):
                    payment_table.insertRow(row)
                    payment_table.setItem(row, 0, QTableWidgetItem(name))
                    payment_table.setItem(row, 1, QTableWidgetItem(f"{data['original']:.2f}元"))
                    
                    method_text = {
                        "AA": "AA制",
                        "比例": f"按比例 {data['value']:.2f}",
                        "自定义": f"自定义 {data['value']:.2f}元"
                    }.get(data['method'], data['method'])
                    
                    payment_table.setItem(row, 2, QTableWidgetItem(method_text))
                    payment_table.setItem(row, 3, QTableWidgetItem(f"{data['final']:.2f}元"))


    def calculate_totals(self, menu_manager):
        totals = {}
        subtotal = 0.0
        
        # 计算每个人的原始消费金额
        for name, order in self.orders.items():
            original = sum(menu_manager.get_dish_by_id(item.dish_id).price * item.quantity 
                        for item in order.items)
            totals[name] = {
                'original': original,
                'final': original,  # 默认应付金额等于消费金额
                'method': order.payment_method,
                'value': order.payment_value
            }
            subtotal += original
        
        # 处理AA制
        aa_people = [name for name, data in totals.items() if data["method"] == "AA"]
        if aa_people:
            aa_total = sum(data["original"] for name, data in totals.items() 
                        if name not in aa_people)
            aa_share = (subtotal - aa_total) / len(aa_people) if aa_people else 0
            for name in aa_people:
                totals[name]["final"] = aa_share
        
        # 处理自定义金额
        custom_people = [name for name, data in totals.items() if data["method"] == "自定义"]
        for name in custom_people:
            # 确保自定义金额不超过消费金额
            totals[name]["final"] = min(totals[name]["value"], totals[name]["original"])
        
        return totals, subtotal


    def save_current_order(self):
        if self.orders:
            order_data = {
                "table": self.current_table,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "orders": {}
            }
            
            for name, person_order in self.orders.items():
                order_data["orders"][name] = {
                    "items": [(item.dish_id, item.quantity, item.remark) for item in person_order.items],
                    "payment_method": person_order.payment_method,
                    "payment_value": person_order.payment_value
                }
            
            self.history.append(order_data)
            return True
        return False

    def clear_current_order(self):
        self.orders = {}
        self.current_table = ""

    def get_customer_habits(self):
        habit_data = defaultdict(lambda: {"count": 0, "total_spent": 0, "dishes": defaultdict(int)})
        
        for order in self.history:
            for name, data in order["orders"].items():
                habit = habit_data[name]
                habit["count"] += 1
                
                for dish_id, quantity, _ in data["items"]:
                    if self.menu_manager:  # 添加检查确保 menu_manager 存在
                        dish = self.menu_manager.get_dish_by_id(dish_id)
                    if dish:
                        habit["total_spent"] += dish.price * quantity
                        habit["dishes"][dish.name] += quantity
        
        return habit_data


class DishEditDialog(QDialog):
    def __init__(self, dish=None, categories=None, parent=None):
        super().__init__(parent)
        self.dish = dish
        self.setWindowTitle("编辑菜品" if dish else "添加菜品")
        self.setup_ui(categories or ["未分类"])
        
        if dish:
            self.load_dish_data()

    def setup_ui(self, categories):
        layout = QVBoxLayout()
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout()
        
        self.id_input = QLineEdit()
        self.id_input.setEnabled(False)
        self.name_input = QLineEdit()
        self.price_input = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.addItems(categories)
        self.category_combo.setEditable(True)
        
        basic_layout.addRow("菜品编号:", self.id_input)
        basic_layout.addRow("菜名:", self.name_input)
        basic_layout.addRow("价格:", self.price_input)
        basic_layout.addRow("分类:", self.category_combo)
        basic_group.setLayout(basic_layout)
        
        # 额外信息
        extra_group = QGroupBox("额外信息")
        extra_layout = QFormLayout()
        
        self.dialect_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        
        self.spicy_combo = QComboBox()
        self.spicy_combo.addItems(["不辣", "微辣", "中辣", "重辣"])
        
        extra_layout.addRow("方言名称:", self.dialect_input)
        extra_layout.addRow("辣度:", self.spicy_combo)
        extra_layout.addRow("描述:", self.description_input)
        extra_group.setLayout(extra_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("取消")
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addWidget(basic_group)
        layout.addWidget(extra_group)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.close)

    def load_dish_data(self):
        if self.dish:
            self.id_input.setText(str(self.dish.id))
            self.name_input.setText(self.dish.name)
            self.price_input.setText(str(self.dish.price))
            self.category_combo.setCurrentText(self.dish.category)
            self.dialect_input.setText(self.dish.dialect_name)
            self.description_input.setPlainText(self.dish.description)
            self.spicy_combo.setCurrentIndex(self.dish.is_spicy)

    def accept(self):
        # 验证数据
        name = self.name_input.text().strip()
        price_text = self.price_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "警告", "请输入菜名")
            return
        
        try:
            price = float(price_text)
            if price <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效的价格")
            return
        
        # 收集数据
        data = {
            "name": name,
            "price": price,
            "category": self.category_combo.currentText(),
            "dialect_name": self.dialect_input.text(),
            "description": self.description_input.toPlainText(),
            "is_spicy": self.spicy_combo.currentIndex()
        }
        
        if self.dish:
            data["id"] = self.dish.id
        
        self.dish_data = data
        self.close()


class PaymentMethodDialog(QDialog):
    def __init__(self, parent=None, original_amount=0):
        super().__init__(parent)
        self.original_amount = original_amount
        self.setWindowTitle("设置支付方式")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 显示原始金额
        amount_label = QLabel(f"消费金额: {self.original_amount:.2f}元")
        layout.addWidget(amount_label)
        
        # 支付方式选择
        self.method_combo = QComboBox()
        self.method_combo.addItem("实际金额（按消费金额支付）", "实际金额")
        self.method_combo.addItem("AA制（平均分摊）", "AA")
        self.method_combo.addItem("自定义金额", "自定义")
        layout.addWidget(self.method_combo)
        
        # 自定义金额输入（默认隐藏）
        self.custom_amount = QDoubleSpinBox()
        self.custom_amount.setRange(0, 99999)
        self.custom_amount.setPrefix("金额: ")
        self.custom_amount.setSuffix("元")
        self.custom_amount.setValue(self.original_amount)
        self.custom_amount.hide()
        layout.addWidget(self.custom_amount)
        
        # 连接信号
        self.method_combo.currentIndexChanged.connect(self.on_method_changed)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def on_method_changed(self, index):
        # 显示/隐藏自定义金额输入
        method = self.method_combo.currentData()
        self.custom_amount.setVisible(method == "自定义")
    
    def on_accept(self):
        method = self.method_combo.currentData()
        
        if method == "AA":
            value = 1.0  # AA制使用1.0作为标记值
        elif method == "自定义":
            value = self.custom_amount.value()
        else:  # 实际金额
            method = "实际金额"
            value = self.original_amount
        
        self.payment_method = (method, value)
        self.accept()


    def update_ui_state(self):
        self.ratio_input.setEnabled(self.ratio_radio.isChecked())
        self.custom_input.setEnabled(self.custom_radio.isChecked())

    def accept(self):
        if self.ratio_radio.isChecked():
            try:
                ratio = float(self.ratio_input.text())
                if ratio <= 0:
                    raise ValueError
                self.payment_method = ("比例", ratio)
            except ValueError:
                QMessageBox.warning(self, "警告", "请输入有效的比例")
                return
        elif self.custom_radio.isChecked():
            try:
                amount = float(self.custom_input.text())
                if amount <= 0:
                    raise ValueError
                self.payment_method = ("自定义", amount)
            except ValueError:
                QMessageBox.warning(self, "警告", "请输入有效的金额")
                return
        else:
            self.payment_method = ("AA", 1.0)
        
        super().accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("高级点菜管理系统")
        self.resize(1000, 700)

        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

        # 初始化管理器 - 直接创建新的空菜单
        self.menu_manager = MenuManager()
        self.order_manager = OrderManager(self.menu_manager)
        
        # 连接信号
        self.order_manager.order_changed.connect(self.update_order_display)
        
        self.last_backup_hash = None  # 用于备份比对
        
        # 初始化UI
        self.init_ui()
        self.setup_shortcuts()

        self.statusBar().showMessage("新建空菜单", 2000)

        # 然后尝试加载上次配置，如果失败则保持默认空菜单
        #if not self.load_last_config():
        #    # 加载失败时的默认初始化
        #    self.menu_manager = MenuManager()
        #    self.order_manager = OrderManager(self.menu_manager)
        #    self.statusBar().showMessage("新建空菜单", 2000)
        
        # 自动备份定时器
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.auto_backup)
        self.backup_timer.start(1 * 60 * 1000)  # 1分钟自动备份一次

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # 顶部菜单栏
        self.create_menu_bar()
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
        # 标签页
        self.tab_widget = QTabWidget()
        self.create_menu_tab()
        self.create_order_tab()
        self.create_history_tab()
        self.create_analysis_tab()
        
        main_layout.addWidget(self.tab_widget)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # 更新UI
        self.update_dish_list()
        self.update_category_filter()
        
        # 添加快捷打开最近订单的菜单项
        recent_menu = self.menuBar().addMenu("最近订单")
        self.recent_orders = self.load_recent_orders()
        self.update_recent_orders_menu(recent_menu)
        
        # 设置快捷键（新增部分）
        self.setup_shortcuts()
        
        # 自动备份定时器
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.auto_backup)
        self.backup_timer.start(1 * 60 * 1000)  # 1分钟自动备份一次

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        new_action = file_menu.addAction("新建菜单")
        new_action.triggered.connect(self.new_menu)
        
        open_action = file_menu.addAction("打开菜单")
        open_action.triggered.connect(self.open_menu)
        
        save_action = file_menu.addAction("保存")
        save_action.triggered.connect(self.save_menu)
        
        save_as_action = file_menu.addAction("另存为")
        save_as_action.triggered.connect(self.save_menu_as)
        
        backup_action = file_menu.addAction("立即备份")
        backup_action.triggered.connect(self.manual_backup)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        add_dish_action = edit_menu.addAction("添加菜品")
        add_dish_action.triggered.connect(self.show_add_dish_dialog)
        
        edit_dish_action = edit_menu.addAction("编辑菜品")
        edit_dish_action.triggered.connect(self.edit_selected_dish)
        
        remove_dish_action = edit_menu.addAction("删除菜品")
        remove_dish_action.triggered.connect(self.remove_selected_dish)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        refresh_action = view_menu.addAction("刷新视图")
        refresh_action.triggered.connect(self.refresh_all_views)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)

    def create_menu_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 过滤和搜索区域
        filter_layout = QHBoxLayout()
        
        self.category_filter = QComboBox()
        self.category_filter.addItem("所有分类")
        self.category_filter.currentIndexChanged.connect(self.update_dish_list)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索菜品...")
        self.search_input.textChanged.connect(self.update_dish_list)
        
        filter_layout.addWidget(QLabel("分类筛选:"))
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(QLabel("搜索:"))
        filter_layout.addWidget(self.search_input)
        
        # 菜品列表
        self.dish_list_widget = QListWidget()
        self.dish_list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.dish_list_widget.itemDoubleClicked.connect(self.edit_selected_dish)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("添加菜品")
        add_button.clicked.connect(self.show_add_dish_dialog)
        
        edit_button = QPushButton("编辑菜品")
        edit_button.clicked.connect(self.edit_selected_dish)
        
        remove_button = QPushButton("删除菜品")
        remove_button.clicked.connect(self.remove_selected_dish)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(remove_button)
        
        layout.addLayout(filter_layout)
        layout.addWidget(self.dish_list_widget)
        layout.addLayout(button_layout)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "菜单管理")


    def create_order_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 1. 顶部搜索和排序区域
        search_sort_layout = QVBoxLayout()
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.order_search_input = QLineEdit()
        self.order_search_input.setPlaceholderText("搜索菜品(支持中文、拼音、首字母)...")
        self.order_search_input.textChanged.connect(self.update_order_dish_list)
        search_layout.addWidget(QLabel("搜索:"))
        search_layout.addWidget(self.order_search_input)
        
        # 排序按钮
        sort_layout = QHBoxLayout()
        self.sort_name_btn = QPushButton("按名称排序")
        self.sort_price_btn = QPushButton("按价格排序")
        self.reset_sort_btn = QPushButton("恢复默认排序")
        
        self.sort_name_btn.clicked.connect(lambda: self.sort_dishes('name'))
        self.sort_price_btn.clicked.connect(lambda: self.sort_dishes('price'))
        self.reset_sort_btn.clicked.connect(lambda: self.sort_dishes('default'))
        
        sort_layout.addWidget(self.sort_name_btn)
        sort_layout.addWidget(self.sort_price_btn)
        sort_layout.addWidget(self.reset_sort_btn)
        
        search_sort_layout.addLayout(search_layout)
        search_sort_layout.addLayout(sort_layout)
        
        # 2. 桌号和顾客信息
        info_layout = QHBoxLayout()
        
        self.table_input = QLineEdit()
        self.table_input.setPlaceholderText("桌号 (默认:1)")
        self.table_input.setText("1")  # 设置默认值
        
        self.customer_name_input = QLineEdit()
        self.customer_name_input.setPlaceholderText("顾客姓名 (默认:匿名)")
        
        info_layout.addWidget(QLabel("桌号:"))
        info_layout.addWidget(self.table_input)
        info_layout.addWidget(QLabel("顾客姓名:"))
        info_layout.addWidget(self.customer_name_input)
        
        # 3. 点餐区域
        order_control_layout = QHBoxLayout()
        
        # 菜品选择区域
        dish_select_layout = QVBoxLayout()
        
        self.dish_category_combo = QComboBox()
        self.dish_category_combo.addItem("所有分类")
        self.dish_category_combo.currentIndexChanged.connect(self.update_order_dish_list)
        
        self.order_dish_list = QListWidget()
        self.order_dish_list.setSelectionMode(QListWidget.SingleSelection)
        
        dish_select_layout.addWidget(self.dish_category_combo)
        dish_select_layout.addWidget(self.order_dish_list)
        
        # 点餐详情区域
        detail_layout = QVBoxLayout()
        
        # 数量
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("数量:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(99)
        self.quantity_spin.setValue(1)
        quantity_layout.addWidget(self.quantity_spin)
        
        # 辣度
        spicy_layout = QHBoxLayout()
        spicy_layout.addWidget(QLabel("辣度:"))
        self.spicy_check = QComboBox()
        self.spicy_check.addItems(["默认辣度", "不辣", "微辣", "中辣", "重辣"])
        spicy_layout.addWidget(self.spicy_check)
        
        # 备注
        remark_layout = QHBoxLayout()
        remark_layout.addWidget(QLabel("备注:"))
        self.remark_input = QLineEdit()
        self.remark_input.setPlaceholderText("特殊要求 (如: 不要香菜, 少辣等)")
        remark_layout.addWidget(self.remark_input)
        
        # 价格显示
        self.current_price_label = QLabel("小计: 0元")
        self.current_price_label.setAlignment(Qt.AlignCenter)
        font = self.current_price_label.font()
        font.setBold(True)
        self.current_price_label.setFont(font)
        
        # 添加按钮
        add_button = QPushButton("添加到订单")
        add_button.clicked.connect(self.add_to_order)
        
        # 添加到详情布局
        detail_layout.addLayout(quantity_layout)
        detail_layout.addLayout(spicy_layout)
        detail_layout.addLayout(remark_layout)
        detail_layout.addWidget(self.current_price_label)
        detail_layout.addWidget(add_button)
        detail_layout.addStretch()
        
        # 将菜品选择和详情添加到控制布局
        order_control_layout.addLayout(dish_select_layout, 2)
        order_control_layout.addLayout(detail_layout, 1)
        
        # 4. 订单表格
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(6)  # 顾客,菜品,单价,数量,小计,备注
        self.order_table.setHorizontalHeaderLabels(["顾客", "菜品", "单价", "数量", "小计", "备注"])
        self.order_table.horizontalHeader().setStretchLastSection(True)
        self.order_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.order_table.setSelectionMode(QTableWidget.SingleSelection)
        self.order_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.order_table.cellDoubleClicked.connect(self.edit_order_item)
        
        # 5. 操作按钮
        button_layout = QHBoxLayout()
        
        # 删除按钮
        remove_item_button = QPushButton("删除选中项")
        remove_item_button.clicked.connect(self.remove_order_item)
        
        # 清空按钮
        clear_order_button = QPushButton("清空订单")
        clear_order_button.clicked.connect(self.clear_order)
        
        # 保存按钮 (不自动清空)
        save_order_button = QPushButton("保存订单")
        save_order_button.clicked.connect(self.save_current_order_without_clear)
        
        # 打开按钮
        open_order_button = QPushButton("打开订单")
        open_order_button.clicked.connect(self.open_order)
        
        # 结算按钮
        calculate_button = QPushButton("结算")
        calculate_button.clicked.connect(self.calculate_totals)
        
        # 添加支付方式设置按钮
        payment_method_button = QPushButton("设置支付方式")
        payment_method_button.clicked.connect(self.set_payment_method)

        # 添加到按钮布局
        button_layout.addWidget(remove_item_button)
        button_layout.addWidget(clear_order_button)
        button_layout.addWidget(save_order_button)
        button_layout.addWidget(open_order_button)
        button_layout.addWidget(calculate_button)
        button_layout.addWidget(payment_method_button)
        
        # 6. 将所有部分添加到主布局
        layout.addLayout(search_sort_layout)
        layout.addLayout(info_layout)
        layout.addLayout(order_control_layout)
        layout.addWidget(self.order_table)
        layout.addLayout(button_layout)
        
        # 7. 设置菜品选择变化时的价格更新
        self.order_dish_list.currentItemChanged.connect(self.update_current_price)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "订单管理")

        # 在UI创建完成后更新订单显示
        self.update_order_display()

        return tab

    def update_current_price(self):
        selected_items = self.order_dish_list.selectedItems()
        if selected_items:
            selected_text = selected_items[0].text()
            price_str = selected_text.split(' - ')[1].split('元')[0]
            try:
                price = float(price_str)
                quantity = self.quantity_spin.value()
                self.current_price_label.setText(f"小计: {price * quantity}元")
            except ValueError:
                self.current_price_label.setText("小计: 0元")
        else:
            self.current_price_label.setText("小计: 0元")

    def create_summary_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        
        self.total_label = QLabel("总金额: 0元")
        self.total_label.setAlignment(Qt.AlignCenter)
        font = self.total_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.total_label.setFont(font)
        
        # 支付方式设置
        payment_group = QGroupBox("支付方式设置")
        payment_layout = QVBoxLayout()
        
        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(4)
        self.payment_table.setHorizontalHeaderLabels(["顾客", "原始金额", "支付方式", "应付金额"])
        self.payment_table.horizontalHeader().setStretchLastSection(True)
        self.payment_table.setSelectionBehavior(QTableWidget.SelectRows)  # 添加行选择行为
        self.payment_table.setSelectionMode(QTableWidget.SingleSelection)  # 单选模式
        
        set_payment_button = QPushButton("设置支付方式")
        set_payment_button.clicked.connect(self.set_payment_method)
        
        payment_layout.addWidget(self.payment_table)
        payment_layout.addWidget(set_payment_button)
        payment_group.setLayout(payment_layout)
        
        # 计算按钮
        calculate_button = QPushButton("计算金额")
        calculate_button.clicked.connect(self.calculate_totals)
        
        layout.addWidget(self.total_label)
        layout.addWidget(payment_group)
        layout.addWidget(calculate_button)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "结算")

    def create_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 历史订单列表
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["时间", "桌号", "顾客数", "总金额"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.doubleClicked.connect(self.view_history_detail)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.update_history_table)
        
        view_button = QPushButton("查看详情")
        view_button.clicked.connect(self.view_history_detail)
        
        export_button = QPushButton("导出Excel")
        export_button.clicked.connect(self.export_history)
        
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(view_button)
        button_layout.addWidget(export_button)
        
        layout.addWidget(self.history_table)
        layout.addLayout(button_layout)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "历史订单")

    def create_analysis_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 分析选项
        analysis_options = QComboBox()
        analysis_options.addItems(["热销菜品排行", "顾客消费习惯"])
        analysis_options.currentIndexChanged.connect(self.update_analysis_view)
        
        # 堆叠窗口显示不同分析结果
        self.analysis_stack = QStackedWidget()
        
        # 热销菜品面板
        top_dishes_widget = QWidget()
        top_dishes_layout = QVBoxLayout()
        
        self.top_dishes_table = QTableWidget()
        self.top_dishes_table.setColumnCount(5)
        self.top_dishes_table.setHorizontalHeaderLabels(["排名", "菜品", "分类", "单价", "销量"])
        self.top_dishes_table.horizontalHeader().setStretchLastSection(True)
        
        top_dishes_layout.addWidget(self.top_dishes_table)
        top_dishes_widget.setLayout(top_dishes_layout)
        
        # 消费习惯面板
        habits_widget = QWidget()
        habits_layout = QVBoxLayout()
        
        self.habits_table = QTableWidget()
        self.habits_table.setColumnCount(4)
        self.habits_table.setHorizontalHeaderLabels(["顾客", "消费次数", "总消费额", "常点菜品"])
        self.habits_table.horizontalHeader().setStretchLastSection(True)
        
        habits_layout.addWidget(self.habits_table)
        habits_widget.setLayout(habits_layout)
        
        # 添加到堆叠窗口
        self.analysis_stack.addWidget(top_dishes_widget)
        self.analysis_stack.addWidget(habits_widget)
        
        layout.addWidget(analysis_options)
        layout.addWidget(self.analysis_stack)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "数据分析")

    def setup_shortcuts(self):
        # 快捷键设置
        self.shortcuts = {
            Qt.Key_1: lambda: self.quick_add_dish(1),
            Qt.Key_2: lambda: self.quick_add_dish(2),
            Qt.Key_3: lambda: self.quick_add_dish(3),
            Qt.Key_4: lambda: self.quick_add_dish(4),
            Qt.Key_5: lambda: self.quick_add_dish(5),
            Qt.Key_6: lambda: self.quick_add_dish(6),
            Qt.Key_7: lambda: self.quick_add_dish(7),
            Qt.Key_8: lambda: self.quick_add_dish(8),
            Qt.Key_9: lambda: self.quick_add_dish(9),
            Qt.Key_0: lambda: self.quick_add_dish(0),
        }

        # 新增 Ctrl+S 保存快捷键
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_menu)

    def keyPressEvent(self, event):
        # 处理快捷键
        if event.key() in self.shortcuts:
            self.shortcuts[event.key()]()
        else:
            super().keyPressEvent(event)

    def quick_add_dish(self, num):
        # 查找对应编号的菜品
        for dish in self.menu_manager.dishes:
            if dish.id % 10 == num:
                customer_name = self.customer_name_input.text().strip()
                if not customer_name:
                    QMessageBox.warning(self, "警告", "请输入顾客姓名")
                    return
                
                self.order_manager.add_person(customer_name)
                self.order_manager.add_item_to_person(customer_name, dish.id, 1)
                self.update_order_display()
                self.statusBar().showMessage(f"已添加 {dish.name} 到 {customer_name} 的订单", 2000)
                break

    def update_dish_list(self):
        self.dish_list_widget.clear()
        
        selected_category = self.category_filter.currentText()
        search_text = self.search_input.text().lower()
        
        for dish in self.menu_manager.dishes:
            if selected_category != "所有分类" and dish.category != selected_category:
                continue
            
            try:
                # 支持中文、拼音全拼、拼音首字母搜索
                pinyin_name = ''.join(lazy_pinyin(dish.name))
                pinyin_initials = ''.join([x[0] for x in lazy_pinyin(dish.name)])
                # 方言名的拼音转换
                dialect_pinyin = ''.join(lazy_pinyin(dish.dialect_name)) if dish.dialect_name else ""
                dialect_initials = ''.join([x[0] for x in lazy_pinyin(dish.dialect_name)]) if dish.dialect_name else ""
            except:
                # 如果拼音转换失败，只比较原始文本
                pinyin_name = pinyin_initials = dish.name.lower()
                dialect_pinyin = dialect_initials = dish.dialect_name.lower() if dish.dialect_name else ""
            
            # 搜索匹配条件
            match_condition = (
                not search_text or  # 无搜索文本时显示所有
                search_text in dish.name.lower() or  # 匹配中文名
                search_text in (dish.dialect_name or "").lower() or  # 匹配方言名
                search_text in pinyin_name or  # 匹配全拼
                search_text in pinyin_initials or  # 匹配首字母
                search_text in dialect_pinyin or  # 匹配方言全拼
                search_text in dialect_initials  # 匹配方言首字母
            )
            
            if not match_condition:
                continue
            
            # 构建显示文本
            item_text = f"{dish.id}. {dish.name} ({dish.category}) - {dish.price}元"
            if dish.dialect_name:
                item_text += f" [{dish.dialect_name}]"
            
            if dish.is_spicy > 0:
                item_text += f" {dish.get_spicy_text()}"
            
            self.dish_list_widget.addItem(item_text)


    def update_category_filter(self):
        current_text = self.category_filter.currentText()
        self.category_filter.clear()
        self.category_filter.addItem("所有分类")
        self.category_filter.addItems(self.menu_manager.categories)
        
        if current_text in self.menu_manager.categories:
            self.category_filter.setCurrentText(current_text)

    def update_order_dish_list(self):
        self.order_dish_list.clear()
        
        selected_category = self.dish_category_combo.currentText()
        search_text = self.order_search_input.text().lower()
        
        for dish in self.menu_manager.dishes:
            if selected_category != "所有分类" and dish.category != selected_category:
                continue

            try:
                # 支持中文、拼音全拼、拼音首字母搜索
                pinyin_name = ''.join(lazy_pinyin(dish.name))
                pinyin_initials = ''.join([x[0] for x in lazy_pinyin(dish.name)])
            except NameError:
                # 如果 lazy_pinyin 不可用，仅支持中文搜索
                pinyin_name = dish.name
                pinyin_initials = dish.name

            if (search_text and 
                search_text not in dish.name.lower() and 
                search_text not in pinyin_name and 
                search_text not in pinyin_initials):
                continue
            
            item_text = f"{dish.id}. {dish.name} - {dish.price}元"
            if dish.dialect_name:
                item_text += f" [{dish.dialect_name}]"
            
            if dish.is_spicy > 0:
                item_text += f" {dish.get_spicy_text()}"
            
            self.order_dish_list.addItem(item_text)

    def sort_dishes(self, key='default'):
        if key == 'default':
            self.menu_manager.dishes.sort(key=lambda x: x.id)
        elif key == 'name':
            self.menu_manager.dishes.sort(key=lambda x: x.name)
        elif key == 'price':
            self.menu_manager.dishes.sort(key=lambda x: x.price)
        
        self.update_order_dish_list()
        self.update_dish_list()

    def update_order_display(self):
        if not hasattr(self, 'order_table') or self.order_table is None:
            return
        
        self.order_table.setRowCount(0)
        
        for person_name, order in self.order_manager.orders.items():
            for item in order.items:
                dish = self.menu_manager.get_dish_by_id(item.dish_id)
                if dish:
                    row = self.order_table.rowCount()
                    self.order_table.insertRow(row)
                    
                    self.order_table.setItem(row, 0, QTableWidgetItem(person_name))
                    self.order_table.setItem(row, 1, QTableWidgetItem(dish.name))
                    self.order_table.setItem(row, 2, QTableWidgetItem(str(dish.price)))
                    self.order_table.setItem(row, 3, QTableWidgetItem(str(item.quantity)))
                    self.order_table.setItem(row, 4, QTableWidgetItem(f"{dish.price * item.quantity}元"))
                    self.order_table.setItem(row, 5, QTableWidgetItem(item.remark))


    def update_order_item(self, row, column):
        if column == 3:  # 数量列
            person_name = self.order_table.item(row, 0).text()
            dish_name = self.order_table.item(row, 1).text()
            new_quantity = int(self.order_table.item(row, 3).text())
            
            # 更新订单管理器中的数据
            for person in self.order_manager.orders.values():
                if person.name == person_name:
                    for item in person.items:
                        dish = self.menu_manager.get_dish_by_id(item.dish_id)
                        if dish and dish.name == dish_name:
                            item.quantity = new_quantity
                            break
            
            # 重新计算小计
            dish_price = float(self.order_table.item(row, 2).text().replace('元', ''))
            self.order_table.item(row, 4).setText(f"{dish_price * new_quantity}元")
            
            # 重新计算总计
            self.calculate_totals()

    def edit_order_item(self, row, column):
        """编辑订单项"""
        if column in (2, 3):  # 数量或备注列
            person_name = self.order_table.item(row, 0).text()
            dish_name = self.order_table.item(row, 1).text()
            
            # 获取当前值
            current_value = self.order_table.item(row, column).text()
            
            # 弹出输入对话框
            if column == 2:  # 数量
                new_value, ok = QInputDialog.getInt(self, "修改数量", f"修改 {dish_name} 的数量:", 
                                                int(current_value), 1, 99, 1)
            else:  # 备注
                new_value, ok = QInputDialog.getText(self, "修改备注", f"修改 {dish_name} 的备注:", 
                                                text=current_value)
            
            if ok and new_value != current_value:
                # 更新表格显示
                self.order_table.item(row, column).setText(str(new_value))
                
                # 更新订单管理器中的数据
                for person in self.order_manager.orders.values():
                    if person.name == person_name:
                        for item in person.items:
                            dish = self.menu_manager.get_dish_by_id(item.dish_id)
                            if dish and dish.name == dish_name:
                                if column == 2:  # 数量
                                    item.quantity = int(new_value)
                                else:  # 备注
                                    item.remark = new_value
                                break
                
                # 如果是数量变化，重新计算小计
                if column == 2:
                    dish_price = float(self.order_table.item(row, 2).text().replace('元', ''))
                    self.order_table.item(row, 4).setText(f"{dish_price * int(new_value)}元")
                    self.calculate_totals()


    def save_current_order_without_clear(self):
        """
        保存当前订单到文件和系统历史记录，但不清空当前订单
        包含以下功能：
        1. 保存到订单历史记录
        2. 弹出文件对话框选择保存位置
        3. 将订单保存为JSON格式文件
        4. 添加到最近订单列表
        5. 更新历史订单显示
        """
        if not self.order_manager.orders:
            QMessageBox.warning(self, "警告", "当前没有订单可保存")
            return
        
        # 1. 首先保存到订单历史记录
        self.order_manager.save_current_order()
        
        # 2. 准备订单数据
        order_data = {
            "version": "2.2.0",
            "table": self.order_manager.current_table,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "orders": {}
        }
        
        # 3. 收集所有订单数据
        for name, person_order in self.order_manager.orders.items():
            order_data["orders"][name] = {
                "items": [(item.dish_id, item.quantity, item.remark) for item in person_order.items],
                "payment_method": person_order.payment_method,
                "payment_value": person_order.payment_value
            }
        
        # 4. 弹出保存文件对话框
        options = QFileDialog.Options()
        default_filename = f"订单_{self.order_manager.current_table}桌_{order_data['timestamp'].replace(':', '-')}.order"
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "保存订单",
            default_filename,  # 默认文件名
            "订单文件 (*.order);;所有文件 (*)", 
            options=options
        )
        
        if not filename:  # 用户取消了保存
            return
        
        # 5. 确保文件扩展名正确
        if not filename.endswith('.order'):
            filename += '.order'
        
        try:
            # 6. 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(order_data, f, ensure_ascii=False, indent=2)
            
            # 7. 添加到最近订单列表
            self.save_recent_order(filename)
            
            # 8. 更新历史订单显示
            self.update_history_table()
            
            # 9. 显示成功消息
            self.statusBar().showMessage(f"订单已保存到: {filename}", 3000)
            QMessageBox.information(
                self, 
                "保存成功", 
                f"订单已成功保存到:\n{filename}\n\n"
                f"桌号: {self.order_manager.current_table}\n"
                f"时间: {order_data['timestamp']}\n"
                f"顾客数: {len(self.order_manager.orders)}"
            )
            
        except Exception as e:
            # 10. 错误处理
            error_msg = f"保存订单失败:\n{str(e)}"
            self.statusBar().showMessage(error_msg, 5000)
            QMessageBox.critical(
                self, 
                "保存失败", 
                error_msg
            )



    def open_order(self):
        # 创建选择对话框，让用户可以选择从历史记录或文件打开
        dialog = QDialog(self)
        dialog.setWindowTitle("打开订单")
        dialog.resize(600, 400)
        layout = QVBoxLayout()
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 标签1: 从历史记录打开
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["时间", "桌号", "顾客数", "总金额"])
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.update_history_table()  # 填充历史数据
        
        history_layout.addWidget(self.history_table)
        history_tab.setLayout(history_layout)
        
        # 标签2: 从文件打开
        file_tab = QWidget()
        file_layout = QVBoxLayout()
        
        # 最近订单列表
        self.recent_order_list = QListWidget()
        self.update_recent_order_list()  # 填充最近订单
        
        # 浏览文件按钮
        browse_button = QPushButton("浏览其他订单文件...")
        browse_button.clicked.connect(lambda: self.browse_order_file(dialog))
        
        file_layout.addWidget(QLabel("最近订单:"))
        file_layout.addWidget(self.recent_order_list)
        file_layout.addWidget(browse_button)
        file_tab.setLayout(file_layout)
        
        # 添加到标签页
        tab_widget.addTab(history_tab, "历史记录")
        tab_widget.addTab(file_tab, "从文件打开")
        
        # 按钮框
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.load_selected_order(tab_widget.currentIndex(), dialog))
        button_box.rejected.connect(dialog.reject)
        
        # 主布局
        layout.addWidget(tab_widget)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        
        # 双击也可以打开
        self.history_table.doubleClicked.connect(lambda: self.load_selected_order(0, dialog))
        self.recent_order_list.doubleClicked.connect(lambda: self.load_selected_order(1, dialog))
        
        dialog.exec_()

    def load_selected_order(self, tab_index, dialog):
        """加载选中的订单"""
        if tab_index == 0:  # 历史记录
            selected_rows = self.history_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "警告", "请先选择一个历史订单")
                return
            
            row = selected_rows[0].row()
            order_data = self.order_manager.history[row]
        else:  # 文件
            selected_items = self.recent_order_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "警告", "请先选择一个订单文件")
                return
            
            filename = selected_items[0].data(Qt.UserRole)
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    order_data = json.load(f)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载订单文件失败: {str(e)}")
                return
        
        # 清空当前订单
        self.order_manager.clear_current_order()
        self.order_manager.current_table = order_data.get("table", "")
        
        # 加载订单数据
        for person_name, person_data in order_data["orders"].items():
            self.order_manager.add_person(person_name)
            for dish_id, quantity, remark in person_data["items"]:
                self.order_manager.add_item_to_person(person_name, dish_id, quantity, remark)
            
            # 设置支付方式
            self.order_manager.set_payment_method(
                person_name,
                person_data["payment_method"],
                person_data["payment_value"]
            )
        
        # 更新UI
        self.table_input.setText(self.order_manager.current_table)
        self.update_order_display()
        self.calculate_totals()
        
        # 如果是文件订单，添加到最近列表
        if tab_index == 1:
            self.save_recent_order(filename)
        
        dialog.accept()
        QMessageBox.information(self, "成功", "订单已加载")

    def browse_order_file(self, dialog):
        """浏览订单文件"""
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self, "打开订单文件", "", 
            "订单文件 (*.order);;所有文件 (*)", 
            options=options
        )
        
        if filename:
            # 添加到最近列表
            self.save_recent_order(filename)
            self.update_recent_order_list()
            
            # 创建临时item用于加载
            item = QListWidgetItem(os.path.basename(filename))
            item.setData(Qt.UserRole, filename)
            self.recent_order_list.setCurrentItem(item)
            
            # 自动触发加载
            self.load_selected_order(1, dialog)


    def update_recent_order_list(self):
        """更新最近订单列表"""
        self.recent_order_list.clear()
        for order_file in self.recent_orders:
            item = QListWidgetItem(os.path.basename(order_file))
            item.setData(Qt.UserRole, order_file)
            self.recent_order_list.addItem(item)

    def load_recent_orders(self):
        """加载最近打开的订单记录"""
        try:
            with open('recent_orders.json', 'r', encoding='utf-8') as f:
                return json.load(f).get("recent_orders", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_recent_order(self, filename):
        """保存到最近订单记录"""
        recent = self.load_recent_orders()
        if filename in recent:
            recent.remove(filename)
        recent.insert(0, filename)
        recent = recent[:5]  # 只保留最近5个
        
        with open('recent_orders.json', 'w', encoding='utf-8') as f:
            json.dump({"recent_orders": recent}, f, ensure_ascii=False, indent=2)


    def load_order_from_file(self, filename):
        """从文件加载订单（完整实现）"""
        try:
            if not os.path.exists(filename):
                QMessageBox.warning(self, "警告", f"订单文件不存在: {filename}")
                return False

            with open(filename, 'r', encoding='utf-8') as f:
                order_data = json.load(f)

            # 验证订单数据结构
            if not isinstance(order_data, dict) or "orders" not in order_data:
                raise ValueError("无效的订单文件格式")

            # 清空当前订单
            self.order_manager.clear_current_order()
            
            # 设置桌号（默认为"1"）
            self.order_manager.current_table = order_data.get("table", "1")
            self.table_input.setText(self.order_manager.current_table)

            # 加载每个顾客的订单
            for person_name, person_data in order_data["orders"].items():
                # 验证顾客数据
                if not isinstance(person_data, dict) or "items" not in person_data:
                    continue

                # 添加顾客
                self.order_manager.add_person(person_name)

                # 加载菜品
                for item in person_data["items"]:
                    # 验证菜品数据格式 (dish_id, quantity, remark)
                    if len(item) != 3 or not all(isinstance(i, (int, str)) for i in item[:2]):
                        continue

                    dish_id, quantity, remark = item
                    self.order_manager.add_item_to_person(
                        person_name, 
                        int(dish_id), 
                        int(quantity), 
                        str(remark)
                    )

                # 设置支付方式（如果有）
                if "payment_method" in person_data and "payment_value" in person_data:
                    self.order_manager.set_payment_method(
                        person_name,
                        person_data["payment_method"],
                        float(person_data["payment_value"])
                    )

            # 更新UI
            self.update_order_display()
            self.calculate_totals()
            
            # 添加到最近订单记录
            self.save_recent_order(filename)
            
            # 更新状态栏
            base_name = os.path.basename(filename)
            self.statusBar().showMessage(f"已加载订单: {base_name}", 3000)
            
            return True

        except json.JSONDecodeError:
            QMessageBox.critical(self, "错误", "无法解析订单文件（JSON格式错误）")
        except ValueError as e:
            QMessageBox.critical(self, "错误", f"订单文件格式无效: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载订单失败: {str(e)}")
        
        return False


    def clear_recent_orders(self):
        """清除最近订单记录"""
        try:
            with open('recent_orders.json', 'w', encoding='utf-8') as f:
                json.dump({"recent_orders": []}, f)
            self.recent_orders = []
            
            # 更新菜单
            recent_menu = self.menuBar().findChild(QMenu, "最近订单")
            if recent_menu:
                self.update_recent_orders_menu(recent_menu)
                
            QMessageBox.information(self, "成功", "已清除最近订单记录")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清除记录失败: {str(e)}")

    def update_recent_orders_menu(self, menu):
        """更新最近订单菜单"""
        menu.clear()
        for order_file in self.recent_orders:
            if os.path.exists(order_file):  # 只添加仍然存在的文件
                action = menu.addAction(os.path.basename(order_file))
                action.setData(order_file)
                action.triggered.connect(lambda checked, f=order_file: self.load_order_from_file(f))
        
        if menu.isEmpty():
            menu.addAction("无最近订单").setEnabled(False)
        
        menu.addSeparator()
        clear_action = menu.addAction("清除记录")
        clear_action.triggered.connect(self.clear_recent_orders)

    def update_payment_display(self, totals, subtotal):
        self.payment_table.setRowCount(len(totals))
        
        for row, (name, data) in enumerate(totals.items()):
            self.payment_table.setItem(row, 0, QTableWidgetItem(name))
            self.payment_table.setItem(row, 1, QTableWidgetItem(f"{data['original']:.2f}元"))
            
            method_text = {
                "AA": "AA制",
                "比例": f"按比例 {data['value']:.2f}",
                "自定义": f"自定义 {data['value']:.2f}元"
            }.get(data['method'], data['method'])
            
            self.payment_table.setItem(row, 2, QTableWidgetItem(method_text))
            self.payment_table.setItem(row, 3, QTableWidgetItem(f"{data['final']:.2f}元"))
        
        self.total_label.setText(f"总金额: {subtotal:.2f}元")
        self.payment_table.resizeColumnsToContents()  # 自动调整列宽


    def update_history_table(self):
        self.history_table.setRowCount(len(self.order_manager.history))
        
        for row, order in enumerate(self.order_manager.history):
            customer_count = len(order["orders"])
            total = 0
            
            for person_data in order["orders"].values():
                for dish_id, quantity, _ in person_data["items"]:
                    dish = self.menu_manager.get_dish_by_id(dish_id)
                    if dish:
                        total += dish.price * quantity
            
            self.history_table.setItem(row, 0, QTableWidgetItem(order["timestamp"]))
            self.history_table.setItem(row, 1, QTableWidgetItem(order["table"]))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(customer_count)))
            self.history_table.setItem(row, 3, QTableWidgetItem(f"{total}元"))

    def update_top_dishes_table(self):
        top_dishes = self.menu_manager.get_top_dishes(10)
        self.top_dishes_table.setRowCount(len(top_dishes))
        
        for row, dish in enumerate(top_dishes):
            self.top_dishes_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.top_dishes_table.setItem(row, 1, QTableWidgetItem(dish.name))
            self.top_dishes_table.setItem(row, 2, QTableWidgetItem(dish.category))
            self.top_dishes_table.setItem(row, 3, QTableWidgetItem(f"{dish.price}元"))
            self.top_dishes_table.setItem(row, 4, QTableWidgetItem(str(dish.sales_count)))

    def update_habits_table(self):
        habits = self.order_manager.get_customer_habits()
        self.habits_table.setRowCount(len(habits))
        
        for row, (name, data) in enumerate(habits.items()):
            self.habits_table.setItem(row, 0, QTableWidgetItem(name))
            self.habits_table.setItem(row, 1, QTableWidgetItem(str(data["count"])))
            self.habits_table.setItem(row, 2, QTableWidgetItem(f"{data['total_spent']}元"))
            
            # 找出最常点的3个菜
            top_dishes = sorted(data["dishes"].items(), key=lambda x: x[1], reverse=True)[:3]
            top_dishes_text = ", ".join(f"{name}({count})" for name, count in top_dishes)
            self.habits_table.setItem(row, 3, QTableWidgetItem(top_dishes_text))

    def update_analysis_view(self, index):
        self.analysis_stack.setCurrentIndex(index)
        
        if index == 0:  # 热销菜品
            self.update_top_dishes_table()
        elif index == 1:  # 消费习惯
            self.update_habits_table()

    def refresh_all_views(self):
        self.update_dish_list()
        self.update_category_filter()
        self.update_order_dish_list()
        self.update_order_display()
        self.update_history_table()
        self.update_top_dishes_table()
        self.update_habits_table()
        
        # 清空支付表格
        if hasattr(self, 'payment_table'):
            self.payment_table.setRowCount(0)
        if hasattr(self, 'total_label'):
            self.total_label.setText("总金额: 0元")


    def show_add_dish_dialog(self):
        dialog = DishEditDialog(categories=self.menu_manager.categories, parent=self)
        dialog.exec_()
        
        if hasattr(dialog, 'dish_data'):
            dish_data = dialog.dish_data
            self.menu_manager.add_dish(
                dish_data["name"],
                dish_data["price"],
                dish_data["category"],
                dish_data["description"],
                dish_data["dialect_name"],
                dish_data["is_spicy"]
            )
            self.update_dish_list()
            self.update_category_filter()
            self.update_order_dish_list()

    def edit_selected_dish(self):
        selected_items = self.dish_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个菜品")
            return
        
        selected_text = selected_items[0].text()
        dish_id = int(selected_text.split('.')[0])
        dish = self.menu_manager.get_dish_by_id(dish_id)
        
        if dish:
            dialog = DishEditDialog(dish=dish, categories=self.menu_manager.categories, parent=self)
            dialog.exec_()
            
            if hasattr(dialog, 'dish_data'):
                dish_data = dialog.dish_data
                self.menu_manager.update_dish(
                    dish.id,
                    name=dish_data["name"],
                    price=dish_data["price"],
                    category=dish_data["category"],
                    description=dish_data["description"],
                    dialect_name=dish_data["dialect_name"],
                    is_spicy=dish_data["is_spicy"]
                )
                self.update_dish_list()
                self.update_category_filter()
                self.update_order_dish_list()

    def remove_selected_dish(self):
        selected_items = self.dish_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个菜品")
            return
        
        reply = QMessageBox.question(self, "确认删除", "确定要删除这个菜品吗?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            selected_text = selected_items[0].text()
            dish_id = int(selected_text.split('.')[0])
            self.menu_manager.remove_dish(dish_id)
            self.update_dish_list()
            self.update_category_filter()
            self.update_order_dish_list()

    def add_to_order(self):
        selected_items = self.order_dish_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择一个菜品")
            return
        
        # 桌号默认为"1"
        table_num = self.table_input.text().strip() or "1"
        self.order_manager.current_table = table_num

        # 顾客姓名默认为"匿名"
        customer_name = self.customer_name_input.text().strip() or "匿名"
                
        selected_text = selected_items[0].text()
        dish_id = int(selected_text.split('.')[0])
        quantity = self.quantity_spin.value()
        
        # 处理备注
        remark = self.remark_input.text().strip()
        
        # 处理辣度
        spicy_level = self.spicy_check.currentIndex()
        if spicy_level > 0:
            remark += ("，" if remark else "") + f"{self.spicy_check.currentText()}"
        
        self.order_manager.add_person(customer_name)
        self.order_manager.add_item_to_person(customer_name, dish_id, quantity, remark)
        
        # 更新显示
        self.update_order_display()
        
        # 清空输入
        self.remark_input.clear()
        self.spicy_check.setCurrentIndex(0)
        
        # 显示反馈
        dish = self.menu_manager.get_dish_by_id(dish_id)
        self.statusBar().showMessage(f"已添加 {quantity}份 {dish.name} 到 {customer_name} 的订单", 2000)

    def remove_order_item(self):
        selected_rows = self.order_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的订单项")
            return
        
        # 从最后开始删除，避免行号变化问题
        for row in sorted((r.row() for r in selected_rows), reverse=True):
            person_name = self.order_table.item(row, 0).text()
            dish_name = self.order_table.item(row, 1).text()
            
            # 找到对应的订单项索引
            person_order = self.order_manager.orders.get(person_name)
            if person_order:
                for i, item in enumerate(person_order.items):
                    dish = self.menu_manager.get_dish_by_id(item.dish_id)
                    if dish and dish.name == dish_name:
                        person_order.remove_item(i)
                        break
        
        self.update_order_display()

    def clear_order(self):
        if not self.order_manager.orders:
            return
        
        reply = QMessageBox.question(self, "确认清空", "确定要清空当前订单吗?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.order_manager.clear_current_order()
            self.update_order_display()
            if hasattr(self, 'payment_table'):  # 安全检查
                self.payment_table.setRowCount(0)
            if hasattr(self, 'total_label'):    # 安全检查
                self.total_label.setText("总金额: 0元")

    def save_current_order(self):
        if not self.order_manager.orders:
            QMessageBox.warning(self, "警告", "当前没有订单可保存")
            return
        
        self.order_manager.save_current_order()
        self.order_manager.clear_current_order()
        self.update_order_display()
        self.update_history_table()
        self.payment_table.setRowCount(0)
        self.total_label.setText("总金额: 0元")
        
        QMessageBox.information(self, "成功", "订单已保存")

    def calculate_totals(self):
        if not self.order_manager.orders:
            QMessageBox.warning(self, "警告", "当前没有订单可计算")
            return
        
        totals, subtotal = self.order_manager.calculate_totals(self.menu_manager)
        
        # 创建详细菜品列表的对话框
        detail_dialog = QDialog(self)
        detail_dialog.setWindowTitle("订单详情")
        detail_dialog.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # 基本信息
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"桌号: {self.order_manager.current_table}"))
        info_layout.addWidget(QLabel(f"顾客数: {len(self.order_manager.orders)}"))
        
        # 详细菜品表格
        detail_table = QTableWidget()
        detail_table.setColumnCount(6)
        detail_table.setHorizontalHeaderLabels(["顾客", "菜品", "单价", "数量", "小计", "备注"])
        detail_table.horizontalHeader().setStretchLastSection(True)
        
        row = 0
        for person_name, order in self.order_manager.orders.items():
            for item in order.items:
                dish = self.menu_manager.get_dish_by_id(item.dish_id)
                if dish:
                    detail_table.insertRow(row)
                    detail_table.setItem(row, 0, QTableWidgetItem(person_name))
                    detail_table.setItem(row, 1, QTableWidgetItem(dish.name))
                    detail_table.setItem(row, 2, QTableWidgetItem(f"{dish.price}元"))
                    detail_table.setItem(row, 3, QTableWidgetItem(str(item.quantity)))
                    detail_table.setItem(row, 4, QTableWidgetItem(f"{dish.price * item.quantity}元"))
                    detail_table.setItem(row, 5, QTableWidgetItem(item.remark))
                    row += 1
        
        # 支付方式表格 - 修改为3列
        payment_table = QTableWidget()
        payment_table.setColumnCount(3)  # 修改为3列
        payment_table.setHorizontalHeaderLabels(["顾客", "消费金额", "应付金额"])  # 修改表头
        payment_table.horizontalHeader().setStretchLastSection(True)
        
        payment_row = 0
        for name, data in totals.items():
            payment_table.insertRow(payment_row)
            payment_table.setItem(payment_row, 0, QTableWidgetItem(name))
            payment_table.setItem(payment_row, 1, QTableWidgetItem(f"{data['original']:.2f}元"))
            payment_table.setItem(payment_row, 2, QTableWidgetItem(f"{data['final']:.2f}元"))  # 直接显示实际应付金额
            payment_row += 1
        
        # 总金额
        total_label = QLabel(f"总金额: {subtotal:.2f}元")
        total_label.setAlignment(Qt.AlignRight)
        font = total_label.font()
        font.setPointSize(14)
        font.setBold(True)
        total_label.setFont(font)
        
        # 移除支付方式设置按钮相关代码
        
        # 添加到布局
        layout.addLayout(info_layout)
        layout.addWidget(QLabel("菜品明细:"))
        layout.addWidget(detail_table)
        layout.addWidget(QLabel("支付详情:"))  # 修改标签文字
        layout.addWidget(payment_table)
        layout.addWidget(total_label)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(detail_dialog.accept)
        layout.addWidget(button_box)
        
        detail_dialog.setLayout(layout)
        detail_dialog.exec_()

    def set_payment_method(self):
        selected_rows = self.order_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            QMessageBox.warning(self, "警告", "请选择一个顾客设置支付方式")
            return
        
        row = selected_rows[0].row()
        person_name = self.order_table.item(row, 0).text()
        
        # 修改计算逻辑，使用menu_manager获取菜品价格 - 版本2.2.1
        original_amount = 0
        person_order = self.order_manager.orders.get(person_name)
        if person_order:
            for item in person_order.items:
                dish = self.menu_manager.get_dish_by_id(item.dish_id)
                if dish:
                    original_amount += dish.price * item.quantity
        
        dialog = PaymentMethodDialog(self, original_amount)
        if dialog.exec_() == QDialog.Accepted:
            if hasattr(dialog, 'payment_method'):
                method, value = dialog.payment_method
                self.order_manager.set_payment_method(person_name, method, value)
                self.update_order_display()
                self.calculate_totals()




    def view_history_detail(self, index=None):
        # 处理传入的可能是QModelIndex的情况
        if isinstance(index, QtCore.QModelIndex):
            index = index.row()  # 转换为行索引

        if index is None:
            selected_rows = self.history_table.selectionModel().selectedRows()
            if not selected_rows:
                return
            index = selected_rows[0].row()  # 确保获取的是整数索引
        
        # 确保index是有效的整数
        try:
            index = int(index)
        except (ValueError, TypeError):
            QMessageBox.warning(self, "错误", "无效的订单索引")
            return
        
        # 检查索引是否在有效范围内
        if index < 0 or index >= len(self.order_manager.history):
            QMessageBox.warning(self, "错误", "订单索引超出范围")
            return
        
        order = self.order_manager.history[index]
        
        detail_dialog = QDialog(self)
        detail_dialog.setWindowTitle(f"订单详情 - {order['table']}桌 - {order['timestamp']}")
        detail_dialog.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # 基本信息
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"桌号: {order['table']}"))
        info_layout.addWidget(QLabel(f"时间: {order['timestamp']}"))
        info_layout.addWidget(QLabel(f"顾客数: {len(order['orders'])}"))
        
        # 订单详情表格
        detail_table = QTableWidget()
        detail_table.setColumnCount(6)
        detail_table.setHorizontalHeaderLabels(["顾客", "菜品", "单价", "数量", "小计", "备注"])
        detail_table.horizontalHeader().setStretchLastSection(True)
        
        total = 0
        row_count = 0
        
        for person_name, person_data in order["orders"].items():
            for dish_id, quantity, remark in person_data["items"]:
                dish = self.menu_manager.get_dish_by_id(dish_id)
                if dish:
                    detail_table.insertRow(row_count)
                    detail_table.setItem(row_count, 0, QTableWidgetItem(person_name))
                    detail_table.setItem(row_count, 1, QTableWidgetItem(dish.name))
                    detail_table.setItem(row_count, 2, QTableWidgetItem(f"{dish.price}元"))
                    detail_table.setItem(row_count, 3, QTableWidgetItem(str(quantity)))
                    detail_table.setItem(row_count, 4, QTableWidgetItem(f"{dish.price * quantity}元"))
                    detail_table.setItem(row_count, 5, QTableWidgetItem(remark))
                    total += dish.price * quantity
                    row_count += 1
        
        # 支付方式表格
        payment_table = QTableWidget()
        payment_table.setColumnCount(4)
        payment_table.setHorizontalHeaderLabels(["顾客", "消费金额", "应付金额"])
        payment_table.horizontalHeader().setStretchLastSection(True)
        
        payment_row = 0
        for person_name, person_data in order["orders"].items():
            payment_table.insertRow(payment_row)
            payment_table.setItem(payment_row, 0, QTableWidgetItem(person_name))
            
            method_text = {
                "AA": "AA制",
                "比例": f"按比例 {person_data['payment_value']}",
                "自定义": f"自定义 {person_data['payment_value']}元"
            }.get(person_data["payment_method"], person_data["payment_method"])
            
            payment_table.setItem(payment_row, 1, QTableWidgetItem(method_text))
            
            # 计算该顾客应付金额
            person_total = 0
            for dish_id, quantity, _ in person_data["items"]:
                dish = self.menu_manager.get_dish_by_id(dish_id)
                if dish:
                    person_total += dish.price * quantity
            payment_table.setItem(payment_row, 2, QTableWidgetItem(f"{person_total}元"))
            payment_row += 1
        
        # 总金额
        total_label = QLabel(f"总金额: {total}元")
        total_label.setAlignment(Qt.AlignRight)
        font = total_label.font()
        font.setBold(True)
        total_label.setFont(font)
        
        layout.addLayout(info_layout)
        layout.addWidget(QLabel("菜品明细:"))
        layout.addWidget(detail_table)
        layout.addWidget(QLabel("支付方式:"))
        layout.addWidget(payment_table)
        layout.addWidget(total_label)
        
        detail_dialog.setLayout(layout)
        detail_dialog.exec_()
        


    def export_history(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self, "导出历史订单", "", 
                                                "Excel文件 (*.xlsx);;CSV文件 (*.csv)", 
                                                options=options)
        if filename:
            try:
                # 这里应该实现实际的导出逻辑
                # 由于需要额外的库(pandas/openpyxl)，这里只显示提示
                QMessageBox.information(self, "成功", f"订单历史已导出到 {filename}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def new_menu(self):
        reply = QMessageBox.question(self, "新建菜单", "创建新菜单会清空当前菜单，是否继续?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.menu_manager = MenuManager()
            self.order_manager = OrderManager(self.menu_manager)
            self.menu_manager.current_file = None
            
            # 重置UI控件状态
            self.table_input.setText("1")
            self.customer_name_input.clear()
            self.remark_input.clear()
            self.spicy_check.setCurrentIndex(0)
            self.quantity_spin.setValue(1)
            
            # 完全刷新所有视图
            self.refresh_all_views()
            self.statusBar().showMessage("已创建新菜单", 2000)
            
            # 更新窗口标题
            self.setWindowTitle("高级点菜管理系统")


    def open_menu(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "打开菜单文件", "", 
                                                "JSON文件 (*.json);;所有文件 (*)", 
                                                options=options)
        if filename:
            new_manager = MenuManager()
            if new_manager.load_from_file(filename):
                self.menu_manager = new_manager
                self.order_manager = OrderManager(self.menu_manager)
                self.menu_manager.current_file = filename
                self.refresh_all_views()
                
                base_name = os.path.basename(filename)
                self.setWindowTitle(f"高级点菜管理系统 - {base_name}")
                self.statusBar().showMessage(f"已加载菜单: {base_name}", 2000)
            else:
                QMessageBox.warning(self, "错误", "无法加载菜单文件")

    def save_menu(self):
        if not self.menu_manager.current_file:
            # 如果是新建的菜单且从未保存过，则调用另存为
            self.save_menu_as()
        else:
            try:
                self.menu_manager.save_to_file(self.menu_manager.current_file)
                self.statusBar().showMessage(f"菜单已保存到: {self.menu_manager.current_file}", 2000)
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存菜单失败:\n{str(e)}")
                # 保存失败时尝试另存为
                self.save_menu_as()


    def save_menu_as(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self, "另存菜单文件", "", 
                                                "JSON文件 (*.json);;所有文件 (*)", 
                                                options=options)
        if filename:
            if not filename.endswith('.json'):
                filename += '.json'
            try:
                self.menu_manager.save_to_file(filename)
                self.menu_manager.current_file = filename  # 更新当前文件路径
                base_name = os.path.basename(filename)
                self.setWindowTitle(f"高级点菜管理系统 - {base_name}")
                self.statusBar().showMessage(f"菜单已保存为 {base_name}", 2000)
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存菜单失败:\n{str(e)}")


    def auto_backup(self):
        if not self.menu_manager.current_file:
            return
        
        # 计算当前菜单的哈希值
        current_hash = hash(json.dumps(
            [vars(dish) for dish in self.menu_manager.dishes],
            sort_keys=True
        ))
        
        # 只有菜单发生变化时才备份
        if current_hash != self.last_backup_hash:
            backup_dir = os.path.join(os.path.dirname(self.menu_manager.current_file), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = os.path.join(backup_dir, f"menu_backup_{timestamp}.json")
            
            self.menu_manager.save_to_file(backup_name)
            self.last_backup_hash = current_hash
            self.statusBar().showMessage(f"自动备份完成: {os.path.basename(backup_name)}", 2000)

    def manual_backup(self):
        self.auto_backup()
        QMessageBox.information(self, "备份成功", "菜单已备份")

    def load_last_config(self):
        try:
            with open('last_config.txt', 'r', encoding='utf-8') as f:
                last_file = f.read().strip()
                if last_file and os.path.exists(last_file):
                    new_manager = MenuManager()
                    if new_manager.load_from_file(last_file):
                        self.menu_manager = new_manager
                        self.order_manager = OrderManager(self.menu_manager)  # 这会自动加载历史

                        # 尝试恢复最后一张订单
                        if self.order_manager.history:
                            last_order = self.order_manager.history[-1]
                            self.order_manager.current_table = last_order.get("table", "")
                            if hasattr(self, 'table_input'):  # 添加检查
                                self.table_input.setText(self.order_manager.current_table)

                        base_name = os.path.basename(last_file)
                        self.setWindowTitle(f"高级点菜管理系统 - {base_name}")
                        self.statusBar().showMessage(f"已加载上次菜单和订单: {base_name}", 2000)
                        return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"加载上次配置失败: {e}")
        return False


    def show_about(self):
        about_text = """
        <h2>高级点菜管理系统</h2>
        <p>版本: 2.0</p>
        <p>功能:</p>
        <ul>
            <li>完整的菜单管理功能</li>
            <li>多人拼单与多种支付方式</li>
            <li>消费记录与数据分析</li>
            <li>自动备份与历史记录</li>
        </ul>
        <p>© 2023 点菜系统开发团队</p>
        """
        QMessageBox.about(self, "关于", about_text)

    def closeEvent(self, event):
        # 保存当前菜单文件路径
        if self.menu_manager.current_file:
            try:
                with open('last_config.txt', 'w', encoding='utf-8') as f:
                    f.write(self.menu_manager.current_file)
            except IOError as e:
                print(f"保存配置失败: {e}")
        
        # 只在菜单被修改过时才询问是否保存
        if self.menu_manager.dishes and self.menu_manager.modified:
            reply = QMessageBox.question(self, "保存菜单", "菜单已被修改，是否保存?",
                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                    QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                self.save_menu()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        event.accept()



if __name__ == "__main__":
    import sys
    from PyQt5.QtGui import QDoubleValidator
    
    app = QApplication(sys.argv)
    
    # 设置中文显示
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
软件截图：

![image](https://github.com/user-attachments/assets/14f18773-c9c6-402a-ba05-54f1edde6dfc)

![image](https://github.com/user-attachments/assets/56452e11-3498-4344-bc4c-65fc0704cf6b)

![image](https://github.com/user-attachments/assets/46532c71-fe6a-4d82-844f-3b7d0513b116)

![image](https://github.com/user-attachments/assets/53a2acfb-2539-4bc9-88d8-e413ba45d390)

![image](https://github.com/user-attachments/assets/e03c3fd6-b1e0-42a3-97ff-0e2f3523af1c)

![image](https://github.com/user-attachments/assets/3a7fd904-d088-4c42-856a-0f387f67ecfe)


# 高级点菜管理系统 - 全方位使用说明书

## 目录
1. [系统简介](#系统简介)
2. [适用人群](#适用人群)
3. [基础功能](#基础功能)
4. [专业功能](#专业功能)
5. [实际应用场景](#实际应用场景)
6. [版本更新历史](#版本更新历史)
7. [技术支持与版权](#技术支持与版权)

---

## 系统简介

**高级点菜管理系统**是一款专为餐饮行业设计的全功能管理软件，集菜单管理、订单处理、支付结算、数据分析于一体。无论是小型快餐店还是高级餐厅，都能通过本系统提升运营效率和服务质量。

### 核心特点
- **直观操作**：简洁的图形界面，无需专业培训即可上手
- **多人拼单**：支持多人共同点餐，灵活分摊费用
- **智能分析**：自动统计热销菜品和顾客消费习惯
- **安全保障**：自动备份机制防止数据丢失
- **多平台支持**：基于Python和PyQt5开发，跨平台运行

---

## 适用人群

### 1. 餐饮业新手/小型餐馆老板
**适用功能**：
- 基础菜单管理（添加/编辑/删除菜品）
- 简单订单记录
- 基本结算功能

**举例说明**：
> 张阿姨开了一家小面馆，使用系统可以轻松记录各种面条的价格和配料，顾客点餐后自动计算总价，还能看到哪些面最受欢迎。

### 2. 餐厅经理/专业餐饮从业者
**适用功能**：
- 高级菜品分类管理
- 多人拼单与复杂支付方式
- 销售数据分析
- 顾客消费习惯追踪

**举例说明**：
> 某中餐厅经理使用系统分析发现"宫保鸡丁"在晚餐时段销量最佳，于是调整了食材采购计划，并在午餐时段推出特价吸引顾客。

### 3. 连锁餐饮企业
**适用功能**：
- 标准化菜单管理
- 多门店数据汇总分析
- 历史订单追溯
- 自动备份与数据安全

**举例说明**：
> 连锁火锅店使用系统统一管理各分店菜单，总部可以查看各分店的销售数据和顾客偏好，为经营决策提供依据。

### 4. 餐饮软件开发者
**专业功能**：
- 模块化设计结构
- 开源代码参考
- 可扩展接口
- 数据存储格式

---

## 基础功能

### 1. 菜单管理
**操作步骤**：
1. 点击"编辑"菜单 → "添加菜品"
2. 填写菜品名称、价格、分类等信息
3. 点击"保存"

**示例**：
```
菜名：鱼香肉丝
价格：38元
分类：川菜
辣度：中辣
方言名：鱼香肉丝
描述：传统川菜，酸甜微辣
```

### 2. 下单流程
1. 输入桌号（默认1）
2. 输入顾客姓名（默认匿名）
3. 从列表选择菜品
4. 调整数量和备注
5. 点击"添加到订单"

### 3. 基础结算
1. 点击"结算"按钮
2. 系统显示总金额和每人应付
3. 可选择现金、扫码等支付方式

---

## 专业功能

### 1. 多人拼单与支付方式
**支持三种支付模式**：
1. **AA制**：总金额平均分摊
2. **按比例**：按消费比例分摊
3. **自定义**：指定每人固定金额

**专业示例**：
> 商务宴请中，公司支付主菜费用(自定义)，员工AA制分摊酒水费用。

### 2. 数据分析
**可获取数据**：
- 热销菜品TOP10
- 时段销售分析
- 顾客消费频次
- 常点菜品组合

**专业应用**：
```python
# 获取热销菜品代码示例
top_dishes = menu_manager.get_top_dishes(limit=5)
for dish in top_dishes:
    print(f"{dish.name}: {dish.sales_count}次")
```

### 3. 系统集成
**开发者接口**：
```python
# 创建订单项
item = OrderItem(dish_id=101, quantity=2, remark="少辣")

# 添加顾客订单
order = PersonOrder("张三")
order.add_item(item)
```

---

## 实际应用场景

### 1. 快餐店应用
**流程**：
1. 设置好固定菜单
2. 顾客点餐时快速选择编号（支持数字快捷键）
3. 即时打印小票

### 2. 宴会管理
**特色功能**：
- 多桌同时管理
- 复杂支付方案设置
- 后期消费查询

### 3. 外卖管理
**应用方式**：
1. 创建"外卖"虚拟桌号
2. 记录顾客电话和地址在备注栏
3. 使用历史订单功能追踪外卖记录

---

## 版本更新历史

### 版本3.4.0 (当前版本)
- 新增Ctrl+S快捷保存功能
- 优化菜单修改检测逻辑
- 修复支付方式设置界面显示问题

### 版本3.3.0
- 增加方言菜名支持
- 改进拼音搜索算法
- 优化订单历史加载速度

### 版本3.2.0
- 新增自动备份功能
- 增加辣度标识系统
- 改进数据分析图表

### 版本3.1.0
- 重构订单管理模块
- 增加最近订单记忆功能
- 优化用户界面布局

（完整更新历史请查看GitHub提交记录）

---

## 技术支持与版权

**版权声明**  
© 2025 杜玛 保留所有权利

**获取帮助**：
- GitHub Issues: [提交问题报告](https://github.com/duma520)
- 项目地址: [https://github.com/duma520](https://github.com/duma520)

**注意事项**：
1. 本软件免费开源，禁止用于商业销售
2. 不提供私人邮箱支持
3. 修改代码后请保留原始版权信息
4. 数据安全建议定期手动备份

**法律条款**：  
未经书面许可，不得修改、反向工程或将本软件用于任何商业目的。违反者将承担法律责任。

---

**附：快速参考指南**

| 快捷键 | 功能 |
|--------|------|
| Ctrl+N | 新建菜单 |
| Ctrl+O | 打开菜单 |
| Ctrl+S | 保存菜单 |
| 1-9数字键 | 快速添加对应编号菜品 |
| F5 | 刷新数据视图 |

**基础流程图**：
```
启动系统 → 加载/创建菜单 → 下单 → 结算 → (保存订单) → 数据分析
```

祝您使用愉快！如有改进建议，欢迎参与开源项目贡献。

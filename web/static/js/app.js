/**
 * 智能家居地图应用 - 科技感2D俯视图
 * 简笔画家具 + 科技感设备图标
 */

const state = {
    homes: [],
    currentHome: null,
    devices: [],
    deletedDeviceIds: new Set(), // 记录已删除的设备ID
    floorPlan: null,
    editMode: false,
    selectedDevice: null,
    selectedRoom: null,
    draggedRoom: null,
    draggedDevice: null,
    dragOffset: { x: 0, y: 0 },
    svg: null,
    tooltip: null
};

let autoRefreshInterval = null;
const AUTO_REFRESH_MS = 3000;

// 房间类型配置 - 科技深色主题
const ROOM_TYPES = {
    living: { name: '客厅', color: 'rgba(0, 128, 255, 0.15)' },
    bedroom: { name: '卧室', color: 'rgba(184, 41, 221, 0.15)' },
    bathroom: { name: '卫生间', color: 'rgba(0, 212, 255, 0.15)' },
    kitchen: { name: '厨房', color: 'rgba(255, 107, 53, 0.15)' },
    balcony: { name: '阳台', color: 'rgba(255, 215, 0, 0.15)' },
    study: { name: '书房', color: 'rgba(0, 255, 136, 0.15)' },
    entry: { name: '玄关', color: 'rgba(128, 128, 128, 0.15)' },
    corridor: { name: '走廊', color: 'rgba(90, 106, 138, 0.15)' },
    room: { name: '房间', color: 'rgba(100, 120, 160, 0.15)' }
};

// 简笔画俯视图家具 - SVG路径（更易识别）
const FURNITURE_PATHS = {
    // 双人床 - 俯视图（明显的枕头和被子分界）
    bed: (w, h) => {
        const hw = w / 2, hh = h / 2;
        return {
            // 床体外框
            main: `M${-hw},${-hh} L${hw},${-hh} L${hw},${hh} L${-hw},${hh} Z`,
            // 被子区域（占2/3）
            quilt: `M${-hw+3},${-hh+3} L${hw-3},${-hh+3} L${hw-3},${hh/3} L${-hw+3},${hh/3} Z`,
            // 枕头区域（占1/3）
            pillowArea: `M${-hw+3},${hh/3+2} L${hw-3},${hh/3+2} L${hw-3},${hh-3} L${-hw+3},${hh-3} Z`,
            // 两个枕头
            pillow1: `M${-hw+8},${hh/3+5} L${-3},${hh/3+5} L${-3},${hh-6} L${-hw+8},${hh-6} Z`,
            pillow2: `M${3},${hh/3+5} L${hw-8},${hh/3+5} L${hw-8},${hh-6} L${3},${hh-6} Z`,
            // 床头板
            headboard: `M${-hw},${hh} L${hw},${hh} L${hw},${hh+5} L${-hw},${hh+5} Z`
        };
    },
    // 床头柜 - 带抽屉把手
    nightstand: () => ({
        // 柜体
        main: `M-12,-10 L12,-10 L12,10 L-12,10 Z`,
        // 顶部
        top: `M-13,-10 L13,-10 L13,-8 L-13,-8 Z`,
        // 抽屉分界线
        drawerLine: `M-12,0 L12,0`,
        // 上抽屉把手
        handle1: `M-3,-5 L3,-5`,
        // 下抽屉把手
        handle2: `M-3,5 L3,5`
    }),
    // L型沙发 - 更明显的L形状
    sofaL: (w, h) => ({
        // 沙发主体L形
        main: `M${-w/2},${-h/2}
                L${w/2-25},${-h/2}
                L${w/2-25},${h/2-25}
                L${w/2},${h/2-25}
                L${w/2},${h/2}
                L${-w/2},${h/2} Z`,
        // 靠背（长边）
        back1: `M${-w/2},${-h/2} L${w/2-25},${-h/2} L${w/2-25},${-h/2+12} L${-w/2},${-h/2+12} Z`,
        // 靠背（短边）
        back2: `M${w/2-25},${h/2-25} L${w/2},${h/2-25} L${w/2},${h/2-12} L${w/2-25},${h/2-12} Z`,
        // 坐垫分割线
        cushion1: `M${-w/2+15},${-h/2+12} L${-w/2+15},${h/2}`,
        cushion2: `M${-w/2+30},${-h/2+12} L${-w/2+30},${h/2}`,
        // 转角坐垫
        corner: `M${w/2-25},${-h/2+12} L${w/2-12},${-h/2+12} L${w/2-12},${h/2-25}`
    }),
    // 直排三人座沙发 - 背部靠墙，面向电视
    // 俯视角度：靠背在左（靠墙），坐垫朝向右侧（电视方向）
    sofa3: (w, h) => ({
        // 沙发主体（长方形）- 宽边在左右，窄边在上下
        main: `M${-h/2},${-w/2} L${h/2},${-w/2} L${h/2},${w/2} L${-h/2},${w/2} Z`,
        // 靠背（左侧，靠墙一侧）
        back: `M${-h/2},${-w/2} L${-h/2+10},${-w/2} L${-h/2+10},${w/2} L${-h/2},${w/2} Z`,
        // 坐垫1（上）
        seat1: `M${-h/2+12},${-w/2+2} L${h/2-2},${-w/2+2} L${h/2-2},${-w/2+w/3-2} L${-h/2+12},${-w/2+w/3-2} Z`,
        // 坐垫2（中）
        seat2: `M${-h/2+12},${-w/2+w/3+2} L${h/2-2},${-w/2+w/3+2} L${h/2-2},${w/2-w/3-2} L${-h/2+12},${w/2-w/3-2} Z`,
        // 坐垫3（下）
        seat3: `M${-h/2+12},${w/2-w/3+2} L${h/2-2},${w/2-w/3+2} L${h/2-2},${w/2-2} L${-h/2+12},${w/2-2} Z`,
        // 扶手（上）
        armT: `M${-h/2+5},${-w/2} L${h/2-5},${-w/2} L${h/2-5},${-w/2+8} L${-h/2+5},${-w/2+8} Z`,
        // 扶手（下）
        armB: `M${-h/2+5},${w/2-8} L${h/2-5},${w/2-8} L${h/2-5},${w/2} L${-h/2+5},${w/2} Z`
    }),
    // 茶几 - 矩形带物品
    coffeeTable: () => ({
        // 桌面
        main: `M-30,-20 L30,-20 L30,20 L-30,20 Z`,
        // 桌面边缘
        edge: `M-32,-20 L32,-20 L32,-18 L-32,-18 Z`,
        // 桌腿（4条）
        leg1: `M-28,-16 L-24,-16 L-24,18 L-28,18 Z`,
        leg2: `M24,-16 L28,-16 L28,18 L24,18 Z`,
        leg3: `M-28,12 L-24,12 L-24,20 L-28,20 Z`,
        leg4: `M24,12 L28,12 L28,20 L24,20 Z`,
        // 茶杯
        cup: `M15,-10 C15,-15 25,-15 25,-10 L25,-5 C25,0 15,0 15,-5 Z`,
        // 茶盘
        tray: `M-20,-5 L-5,-5 L-5,8 L-20,8 Z`
    }),
    // 电视柜 - 长条形带抽屉和电视
    tvStand: (w) => ({
        // 柜体
        main: `M${-w/2},-10 L${w/2},-10 L${w/2},15 L${-w/2},15 Z`,
        // 顶部
        top: `M${-w/2-2},-10 L${w/2+2},-10 L${w/2+2},-7 L${-w/2-2},-7 Z`,
        // 抽屉分隔
        drawers: `M${-w/4},-7 L${-w/4},15 M${0},-7 L${0},15 M${w/4},-7 L${w/4},15`,
        // 把手
        handles: `M${-w/4+3},4 L${-w/4-3},4 M${3},4 L${-3},4 M${w/4+3},4 L${w/4-3},4`,
        // 电视底座
        tvBase: `M-8,-20 L8,-20 L6,-10 L-6,-10 Z`,
        // 电视屏幕
        tv: `M-20,-35 L20,-35 L20,-20 L-20,-20 Z`
    }),
    // 橱柜 - L型厨房台面
    cabinet: (w, h) => ({
        // L型主体
        main: `M${-w/2},${-h/2}
                L${w/2-30},${-h/2}
                L${w/2-30},${h/2}
                L${-w/2},${h/2} Z`,
        // 转角柜
        corner: `M${w/2-30},${-h/2} L${w/2},${-h/2} L${w/2},${-h/2+30} L${w/2-30},${-h/2+30} Z`,
        // 灶台区域
        stove: `M${w/2-28},${-h/2+2} L${w/2-2},${-h/2+2} L${w/2-2},${-h/2+28} L${w/2-28},${-h/2+28} Z`,
        // 灶眼
        burner1: `M${w/2-22},${-h/2+8} L${w/2-8},${-h/2+8} M${w/2-15},${-h/2+5} L${w/2-15},${-h/2+11}`,
        // 水槽
        sink: `M${-w/4},0 L${w/4},0 L${w/4},${h/2-5} L${-w/4},${h/2-5} Z`,
        // 柜门分割线
        doors: `M0,${-h/2} L0,${h/2} M${-w/4},${-h/2} L${-w/4},0 M${w/4},${-h/2} L${w/4},0`
    }),
    // 冰箱 - 双门立式
    fridge: () => ({
        // 主体
        main: `M-15,-30 L15,-30 L15,30 L-15,30 Z`,
        // 上门（冷藏）
        top: `M-15,-30 L15,-30 L15,-2 L-15,-2 Z`,
        // 下门（冷冻）
        bottom: `M-15,-2 L15,-2 L15,30 L-15,30 Z`,
        // 门把手
        handle1: `M10,-25 L12,-25 L12,-8 L10,-8 Z`,
        handle2: `M10,4 L12,4 L12,25 L10,25 Z`,
        // 显示屏
        screen: `M-5,-20 L5,-20 L5,-15 L-5,-15 Z`,
        // 品牌标识
        logo: `M-3,10 L3,10 M0,7 L0,13`
    }),
    // 马桶 - 标准坐便器俯视图
    toilet: () => ({
        // 水箱
        tank: `M-10,-18 L10,-18 L10,-6 L-10,-6 Z`,
        // 水箱盖
        tankLid: `M-11,-18 L11,-18 L11,-20 L-11,-20 Z`,
        // 马桶座圈（椭圆）
        seat: `M-12,-6 C-16,-6 -16,10 -12,10 L12,10 C16,10 16,-6 12,-6 Z`,
        // 马桶盖（开启状态示意）
        lid: `M-10,-6 L10,-6 L8,2 L-8,2 Z`,
        // 冲水按钮
        flush: `M0,-14 C-2,-14 -2,-12 0,-12 C2,-12 2,-14 0,-14`
    }),
    // 洗手台 - 带镜子和水龙头
    sink: () => ({
        // 洗手台柜体
        cabinet: `M-25,-5 L25,-5 L25,20 L-25,20 Z`,
        // 台面
        counter: `M-28,-8 L28,-8 L28,-5 L-28,-5 Z`,
        // 洗手盆（椭圆）
        basin: `M-18,-2 C-22,-2 -22,12 -18,12 L18,12 C22,12 22,-2 18,-2 Z`,
        // 水龙头
        faucet: `M0,-5 L0,-15 L8,-20`,
        // 龙头底座
        faucetBase: `M-3,-5 L3,-5 L3,-2 L-3,-2 Z`,
        // 镜子
        mirror: `M-20,-22 L20,-22 L20,-10 L-20,-10 Z`,
        mirrorFrame: `M-22,-24 L22,-24 L22,-8 L-22,-8 Z`
    }),
    // 淋浴区 - 带花洒和地漏
    shower: () => ({
        // 淋浴区边框
        area: `M-25,-25 L25,-25 L25,25 L-25,25 Z`,
        // 防滑地砖纹路
        tiles: `M-25,-15 L25,-15 M-25,0 L25,0 M-25,15 L25,15 M0,-25 L0,25 M-15,-25 L-15,25 M15,-25 L15,25`,
        // 花洒杆
        showerRod: `M15,-25 L15,-5`,
        // 花洒头
        showerHead: `M10,-5 L20,-5 L18,0 L12,0 Z`,
        // 控制阀
        valve: `M15,-15 C13,-15 13,-13 15,-13 C17,-13 17,-15 15,-15`,
        // 地漏
        drain: `M-5,20 L5,20 L3,23 L-3,23 Z`,
        drainHoles: `M-2,21 L2,21 M0,20 L0,23`
    }),
    // 书桌 - 带抽屉和椅子
    desk: () => ({
        // 桌面
        top: `M-50,-15 L50,-15 L50,-12 L-50,-12 Z`,
        // 桌面主体
        main: `M-50,-12 L50,-12 L50,15 L-50,15 Z`,
        // 左侧抽屉柜
        drawers: `M-50,-12 L-30,-12 L-30,15 L-50,15 Z`,
        drawerLines: `M-50,-5 L-30,-5 M-50,5 L-30,-5`,
        // 抽屉把手
        handles: `M-42,-3 L-38,-3 M-42,7 L-38,7`,
        // 右侧腿部空间
        legR: `M30,15 L35,15 L35,25 L30,25 Z`,
        legL: `M-30,15 L-25,15 L-25,25 L-30,25 Z`,
        // 椅子
        chairSeat: `M-15,25 L15,25 L12,35 L-12,35 Z`,
        chairBack: `M-15,35 L15,35 L15,45 L-15,45 Z`
    }),
    // 书架 - 多层带书
    bookshelf: (h) => ({
        // 外框
        main: `M-10,${-h/2} L10,${-h/2} L10,${h/2} L-10,${h/2} Z`,
        // 层板（4层）
        shelf1: `M-10,${-h/2+h/5} L10,${-h/2+h/5}`,
        shelf2: `M-10,${-h/2+2*h/5} L10,${-h/2+2*h/5}`,
        shelf3: `M-10,${-h/2+3*h/5} L10,${-h/2+3*h/5}`,
        shelf4: `M-10,${-h/2+4*h/5} L10,${-h/2+4*h/5}`,
        // 书（第一层）
        book1: `M-8,${-h/2+3} L-5,${-h/2+3} L-5,${-h/2+h/5-1} L-8,${-h/2+h/5-1} Z`,
        book2: `M-3,${-h/2+2} L0,${-h/2+2} L0,${-h/2+h/5-1} L-3,${-h/2+h/5-1} Z`,
        book3: `M3,${-h/2+4} L7,${-h/2+4} L7,${-h/2+h/5-1} L3,${-h/2+h/5-1} Z`
    }),
    // 洗衣机 - 滚筒式
    washer: () => ({
        // 机身
        main: `M-20,-25 L20,-25 L20,25 L-20,25 Z`,
        // 顶部面板
        top: `M-20,-25 L20,-25 L20,-18 L-20,-18 Z`,
        // 控制面板
        control: `M-18,-23 L18,-23 L18,-20 L-18,-20 Z`,
        // 旋钮
        knob: `M0,-21.5 C-2,-21.5 -2,-19.5 0,-19.5 C2,-19.5 2,-21.5 0,-21.5`,
        // 舱门（圆形）
        door: `M0,2 C-12,2 -12,18 -12,18 L12,18 C12,18 12,2 0,2`,
        doorRing: `M0,10 C-8,10 -8,18 -8,18 L8,18 C8,18 8,10 0,10`,
        // 显示屏
        display: `M8,-23 L15,-23 L15,-20 L8,-20 Z`
    }),
    // 鞋柜 - 多层带门
    shoeCabinet: (w) => ({
        // 柜体
        main: `M${-w/2},-8 L${w/2},-8 L${w/2},8 L${-w/2},8 Z`,
        // 顶部
        top: `M${-w/2-1},-8 L${w/2+1},-8 L${w/2+1},-6 L${-w/2-1},-6 Z`,
        // 柜门分割线（3门）
        door1: `M${-w/2+3},-8 L${-w/2+3},8`,
        door2: `M${-w/6},-8 L${-w/6},8`,
        door3: `M${w/2-3},-8 L${w/2-3},8`,
        // 把手
        handle1: `M${-w/3},0 L${-w/3+2},0`,
        handle2: `M${-1},0 L${1},0`,
        handle3: `M${w/3-2},0 L${w/3},0`
    }),
    // 植物 - 盆栽
    plant: () => ({
        // 花盆
        pot: `M-8,5 L8,5 L6,12 L-6,12 Z`,
        potTop: `M-10,5 L10,5 L10,2 L-10,2 Z`,
        // 植物（多片叶子）
        leaf1: `M0,5 Q-10,-5 -5,-15 Q0,-5 0,5`,
        leaf2: `M0,5 Q10,-5 5,-15 Q0,-5 0,5`,
        leaf3: `M0,5 Q-6,-8 -8,-12 Q-3,-5 0,5`,
        leaf4: `M0,5 Q6,-8 8,-12 Q3,-5 0,5`,
        leaf5: `M0,5 Q0,-15 0,-18`
    })
};

// 真实设备外观图标SVG - 基于小米/主流智能家居设备设计
const DEVICE_ICON_SVGS = {
    // 智能吸顶灯 - 圆形平板灯设计
    light: `<g transform="scale(0.55)">
        <!-- 灯体外圈 -->
        <ellipse cx="0" cy="0" rx="26" ry="26" fill="#F5F5F5" stroke="#E0E0E0" stroke-width="1"/>
        <!-- 发光面板 -->
        <ellipse cx="0" cy="0" rx="22" ry="22" fill="#FFF" stroke="#00D4FF" stroke-width="2"/>
        <!-- 中央装饰 -->
        <circle cx="0" cy="0" r="8" fill="none" stroke="#00D4FF" stroke-width="1.5" opacity="0.6"/>
        <!-- 光线效果 -->
        <line x1="-18" y1="0" x2="-14" y2="0" stroke="#FFD700" stroke-width="2" opacity="0.8"/>
        <line x1="14" y1="0" x2="18" y2="0" stroke="#FFD700" stroke-width="2" opacity="0.8"/>
        <line x1="0" y1="-18" x2="0" y2="-14" stroke="#FFD700" stroke-width="2" opacity="0.8"/>
        <line x1="0" y1="14" x2="0" y2="18" stroke="#FFD700" stroke-width="2" opacity="0.8"/>
    </g>`,

    // 台灯 - 小米台灯设计风格
    lamp: `<g transform="scale(0.5)">
        <!-- 底座 -->
        <ellipse cx="0" cy="22" rx="14" ry="6" fill="#FFF" stroke="#DDD" stroke-width="1"/>
        <!-- 灯杆 -->
        <line x1="0" y1="22" x2="0" y2="-5" stroke="#F0F0F0" stroke-width="4"/>
        <line x1="0" y1="15" x2="-8" y2="-8" stroke="#F0F0F0" stroke-width="3"/>
        <!-- 灯头 -->
        <path d="M-12,-8 L8,-8 L12,5 L-16,5 Z" fill="#FFF" stroke="#00D4FF" stroke-width="2"/>
        <!-- 发光面 -->
        <ellipse cx="-2" cy="5" rx="10" ry="4" fill="#00D4FF" opacity="0.3"/>
        <!-- 红色装饰条 -->
        <rect x="-2" y="8" width="4" height="3" fill="#FF4444"/>
    </g>`,

    // 空调 - 小米空调挂机外观
    ac: `<g transform="scale(0.6)">
        <!-- 机身 -->
        <rect x="-35" y="-12" width="70" height="24" rx="3" fill="#FFF" stroke="#E0E0E0" stroke-width="1"/>
        <!-- 顶部进风口 -->
        <line x1="-32" y1="-8" x2="32" y2="-8" stroke="#DDD" stroke-width="1"/>
        <!-- 正面面板 -->
        <rect x="-30" y="-6" width="60" height="16" rx="2" fill="#FAFAFA"/>
        <!-- LED显示屏 -->
        <rect x="18" y="-4" width="10" height="6" rx="1" fill="#00D4FF" opacity="0.8"/>
        <!-- 出风口 -->
        <rect x="-28" y="10" width="56" height="4" rx="1" fill="#333"/>
        <!-- 品牌标识位置 -->
        <circle cx="-20" cy="2" r="3" fill="none" stroke="#CCC" stroke-width="1"/>
    </g>`,

    // 摄像头 - 小米摄像头球机设计
    camera: `<g transform="scale(0.55)">
        <!-- 底座 -->
        <ellipse cx="0" cy="18" rx="10" ry="4" fill="#FFF" stroke="#DDD" stroke-width="1"/>
        <!-- 支架 -->
        <rect x="-4" y="8" width="8" height="10" fill="#F0F0F0"/>
        <!-- 球形外壳 -->
        <circle cx="0" cy="0" r="18" fill="#FFF" stroke="#E0E0E0" stroke-width="1"/>
        <!-- 黑色镜头圈 -->
        <circle cx="0" cy="0" r="14" fill="#1a1a1a"/>
        <!-- 镜头 -->
        <circle cx="0" cy="0" r="8" fill="#0a0a0a"/>
        <!-- 镜头反光 -->
        <circle cx="2" cy="-2" r="3" fill="#00D4FF" opacity="0.6"/>
        <!-- 状态指示灯 -->
        <circle cx="12" cy="-12" r="2" fill="#00FF88"/>
        <!-- 麦克风孔 -->
        <circle cx="-10" cy="10" r="1.5" fill="#666"/>
    </g>`,

    // 音箱 - 小爱音箱设计风格
    speaker: `<g transform="scale(0.55)">
        <!-- 底座 -->
        <ellipse cx="0" cy="18" rx="16" ry="5" fill="#333"/>
        <!-- 机身 -->
        <rect x="-15" y="-18" width="30" height="36" rx="6" fill="#FFF" stroke="#E0E0E0" stroke-width="1"/>
        <!-- 网布纹理示意 -->
        <line x1="-10" y1="-12" x2="10" y2="-12" stroke="#F0F0F0" stroke-width="1"/>
        <line x1="-12" y1="-6" x2="12" y2="-6" stroke="#F0F0F0" stroke-width="1"/>
        <line x1="-12" y1="0" x2="12" y2="0" stroke="#F0F0F0" stroke-width="1"/>
        <line x1="-12" y1="6" x2="12" y2="6" stroke="#F0F0F0" stroke-width="1"/>
        <!-- 顶部控制区 -->
        <ellipse cx="0" cy="-14" rx="10" ry="3" fill="#F8F8F8" stroke="#E0E0E0" stroke-width="1"/>
        <!-- 指示灯环 -->
        <ellipse cx="0" cy="-14" rx="6" ry="2" fill="none" stroke="#00D4FF" stroke-width="1.5" opacity="0.8"/>
        <!-- 音量减号 -->
        <rect x="-8" y="10" width="6" height="2" fill="#CCC"/>
        <!-- 音量加号 -->
        <rect x="2" y="10" width="6" height="2" fill="#CCC"/>
        <rect x="4" y="8" width="2" height="6" fill="#CCC"/>
    </g>`,

    // 窗帘 - 智能窗帘电机+轨道
    curtain: `<g transform="scale(0.6)">
        <!-- 轨道 -->
        <rect x="-20" y="-22" width="40" height="4" fill="#DDD"/>
        <!-- 左窗帘 -->
        <rect x="-20" y="-18" width="16" height="36" fill="#E8E8E8" stroke="#CCC" stroke-width="1"/>
        <line x1="-20" y1="-10" x2="-4" y2="-10" stroke="#DDD" stroke-width="1"/>
        <line x1="-20" y1="-2" x2="-4" y2="-2" stroke="#DDD" stroke-width="1"/>
        <line x1="-20" y1="6" x2="-4" y2="6" stroke="#DDD" stroke-width="1"/>
        <line x1="-20" y1="14" x2="-4" y2="14" stroke="#DDD" stroke-width="1"/>
        <!-- 右窗帘 -->
        <rect x="4" y="-18" width="16" height="36" fill="#E8E8E8" stroke="#CCC" stroke-width="1"/>
        <line x1="4" y1="-10" x2="20" y2="-10" stroke="#DDD" stroke-width="1"/>
        <line x1="4" y1="-2" x2="20" y2="-2" stroke="#DDD" stroke-width="1"/>
        <line x1="4" y1="6" x2="20" y2="6" stroke="#DDD" stroke-width="1"/>
        <line x1="4" y1="14" x2="20" y2="14" stroke="#DDD" stroke-width="1"/>
        <!-- 电机 -->
        <rect x="-3" y="-24" width="6" height="8" rx="1" fill="#FFF" stroke="#00D4FF" stroke-width="1"/>
        <circle cx="0" cy="-20" r="1.5" fill="#00D4FF"/>
    </g>`,

    // 智能门锁 - 指纹锁外观
    lock: `<g transform="scale(0.55)">
        <!-- 前面板外框 -->
        <rect x="-12" y="-28" width="24" height="56" rx="4" fill="#1a1a1a" stroke="#333" stroke-width="1"/>
        <!-- 把手 -->
        <path d="M12,-5 L22,-5 L22,5 L12,5" fill="none" stroke="#C0A040" stroke-width="4"/>
        <!-- 指纹识别区 -->
        <ellipse cx="0" cy="12" rx="6" ry="8" fill="#2a2a2a" stroke="#444" stroke-width="1"/>
        <ellipse cx="0" cy="12" rx="3" ry="4" fill="none" stroke="#00D4FF" stroke-width="1" opacity="0.6"/>
        <!-- 密码键盘区 -->
        <rect x="-8" y="-20" width="16" height="12" rx="2" fill="#2a2a2a"/>
        <!-- 门铃按钮 -->
        <circle cx="0" cy="-24" r="2" fill="#00FF88"/>
        <!-- 状态灯 -->
        <circle cx="8" cy="-24" r="1.5" fill="#00D4FF" opacity="0.8"/>
    </g>`,

    // 冰箱 - 双开门智能冰箱
    fridge: `<g transform="scale(0.5)">
        <!-- 机身 -->
        <rect x="-16" y="-32" width="32" height="64" rx="3" fill="#F8F8F8" stroke="#E0E0E0" stroke-width="1"/>
        <!-- 上下门分界线 -->
        <line x1="-16" y1="0" x2="16" y2="0" stroke="#DDD" stroke-width="2"/>
        <!-- 上门（冷藏） -->
        <rect x="-14" y="-30" width="28" height="28" rx="2" fill="#FFF"/>
        <!-- 下门（冷冻） -->
        <rect x="-14" y="2" width="28" height="28" rx="2" fill="#FFF"/>
        <!-- 上门把手 -->
        <rect x="10" y="-25" width="3" height="18" rx="1" fill="#DDD"/>
        <!-- 下门把手 -->
        <rect x="10" y="7" width="3" height="18" rx="1" fill="#DDD"/>
        <!-- 显示屏 -->
        <rect x="-6" y="-22" width="12" height="8" rx="1" fill="#1a1a1a"/>
        <text x="0" y="-16" text-anchor="middle" font-size="5" fill="#00D4FF" font-family="Arial">4°C</text>
        <!-- 品牌标识 -->
        <circle cx="0" cy="-28" r="2" fill="none" stroke="#CCC" stroke-width="1"/>
    </g>`,

    // 电视 - 平板电视外观
    tv: `<g transform="scale(0.55)">
        <!-- 屏幕外框 -->
        <rect x="-28" y="-16" width="56" height="32" rx="2" fill="#1a1a1a" stroke="#333" stroke-width="1"/>
        <!-- 屏幕显示区 -->
        <rect x="-26" y="-14" width="52" height="28" rx="1" fill="#0a0a0a"/>
        <!-- 屏幕反光效果 -->
        <polygon points="-26,-14 -10,-14 -26,2" fill="#222" opacity="0.5"/>
        <!-- 底座 -->
        <polygon points="-8,16 8,16 12,22 -12,22" fill="#333"/>
        <!-- 指示灯 -->
        <circle cx="20" cy="14" r="1.5" fill="#00D4FF" opacity="0.8"/>
        <!-- 品牌LOGO位置 -->
        <rect x="-6" y="12" width="12" height="2" fill="#333"/>
    </g>`,

    // 开关面板 - 86型智能开关
    switch: `<g transform="scale(0.6)">
        <!-- 面板底框 -->
        <rect x="-12" y="-18" width="24" height="36" rx="3" fill="#FFF" stroke="#E0E0E0" stroke-width="1"/>
        <!-- 按键区域 -->
        <rect x="-9" y="-15" width="18" height="12" rx="2" fill="#F8F8F8" stroke="#EEE" stroke-width="1"/>
        <rect x="-9" y="-1" width="18" height="12" rx="2" fill="#F8F8F8" stroke="#EEE" stroke-width="1"/>
        <!-- 指示灯 -->
        <circle cx="6" y="-9" r="1.5" fill="#00FF88" opacity="0.8"/>
        <circle cx="6" cy="5" r="1.5" fill="#00FF88" opacity="0.8"/>
        <!-- 触控标识 -->
        <line x1="-4" y1="-12" x2="-4" y2="-6" stroke="#CCC" stroke-width="1"/>
        <line x1="0" y1="-12" x2="0" y2="-6" stroke="#CCC" stroke-width="1"/>
        <line x1="4" y1="-12" x2="4" y2="-6" stroke="#CCC" stroke-width="1"/>
    </g>`,

    // 空气净化器 - 小米净化器设计
    purifier: `<g transform="scale(0.55)">
        <!-- 底座 -->
        <ellipse cx="0" cy="20" rx="14" ry="5" fill="#FFF" stroke="#DDD" stroke-width="1"/>
        <!-- 机身圆柱 -->
        <rect x="-14" y="-22" width="28" height="42" rx="4" fill="#FFF" stroke="#E0E0E0" stroke-width="1"/>
        <!-- 进风口格栅 -->
        <line x1="-12" y1="-12" x2="12" y2="-12" stroke="#F0F0F0" stroke-width="1"/>
        <line x1="-13" y1="-6" x2="13" y2="-6" stroke="#F0F0F0" stroke-width="1"/>
        <line x1="-13" y1="0" x2="13" y2="0" stroke="#F0F0F0" stroke-width="1"/>
        <line x1="-13" y1="6" x2="13" y2="6" stroke="#F0F0F0" stroke-width="1"/>
        <line x1="-12" y1="12" x2="12" y2="12" stroke="#F0F0F0" stroke-width="1"/>
        <!-- OLED显示屏 -->
        <circle cx="0" cy="-16" r="5" fill="#1a1a1a"/>
        <text x="0" y="-14" text-anchor="middle" font-size="4" fill="#00D4FF" font-family="Arial">35</text>
        <!-- 出风口 -->
        <ellipse cx="0" cy="-22" rx="10" ry="2" fill="#F8F8F8" stroke="#DDD" stroke-width="1"/>
        <!-- 指示灯 -->
        <circle cx="10" y="-8" r="1.5" fill="#00FF88"/>
    </g>`,

    // 未知设备
    unknown: `<g transform="scale(0.6)">
        <rect x="-12" y="-12" width="24" height="24" rx="4" fill="#666" stroke="#888" stroke-width="2"/>
        <text x="0" y="4" text-anchor="middle" fill="#FFF" font-size="14" font-weight="bold">?</text>
    </g>`,

    // 中控屏/智能平板 - iPad设计风格
    pad: `<g transform="scale(0.55)">
        <!-- 设备外框 - 圆角矩形，等边窄边框 -->
        <rect x="-24" y="-32" width="48" height="64" rx="5" fill="#2a2a2a" stroke="#1a1a1a" stroke-width="2"/>
        <!-- 屏幕显示区 - 大屏占比，四边等宽边框 -->
        <rect x="-21" y="-29" width="42" height="54" rx="3" fill="#000"/>
        <!-- 屏幕反光效果 -->
        <polygon points="-21,-29 0,-29 -21,-12" fill="#1a1a1a" opacity="0.6"/>
        <!-- 屏幕壁纸/背景 -->
        <rect x="-21" y="-29" width="42" height="54" rx="3" fill="#0d1b2a" opacity="0.8"/>
        <!-- 应用图标网格 -->
        <!-- 第一行 -->
        <rect x="-18" y="-25" width="8" height="8" rx="2" fill="#007AFF"/>
        <rect x="-7" y="-25" width="8" height="8" rx="2" fill="#34C759"/>
        <rect x="4" y="-25" width="8" height="8" rx="2" fill="#FF9500"/>
        <!-- 第二行 -->
        <rect x="-18" y="-14" width="8" height="8" rx="2" fill="#FF3B30"/>
        <rect x="-7" y="-14" width="8" height="8" rx="2" fill="#5856D6"/>
        <rect x="4" y="-14" width="8" height="8" rx="2" fill="#FF2D55"/>
        <!-- 底部Dock栏 -->
        <rect x="-21" y="0" width="42" height="12" rx="2" fill="#1a1a1a" opacity="0.5"/>
        <rect x="-18" y="2" width="8" height="8" rx="2" fill="#5AC8FA"/>
        <rect x="-7" y="2" width="8" height="8" rx="2" fill="#FFCC00"/>
        <rect x="4" y="2" width="8" height="8" rx="2" fill="#AF52DE"/>
        <!-- Home键（传统iPad设计） -->
        <circle cx="0" cy="28" r="3" fill="#1a1a1a" stroke="#3a3a3a" stroke-width="1"/>
        <circle cx="0" cy="28" r="1.5" fill="none" stroke="#666" stroke-width="0.5"/>
        <!-- 前置摄像头 -->
        <circle cx="0" cy="-30" r="1" fill="#1a1a1a"/>
    </g>`
};

// 获取设备图标SVG
function getDeviceIconSvg(model) {
    const m = (model || '').toLowerCase();
    // 优先检查特定关键词（顺序很重要）
    if (m.includes('camera')) return DEVICE_ICON_SVGS.camera;
    if (m.includes('pad') || m.includes('screen') || m.includes('panel')) return DEVICE_ICON_SVGS.pad;
    if (m.includes('light') || m.includes('lamp')) {
        if (m.includes('lamp')) return DEVICE_ICON_SVGS.lamp;
        return DEVICE_ICON_SVGS.light;
    }
    if (m.includes('air') || m.includes('ac') || m.includes('conditioner')) return DEVICE_ICON_SVGS.ac;
    if (m.includes('speaker')) return DEVICE_ICON_SVGS.speaker;
    if (m.includes('curtain')) return DEVICE_ICON_SVGS.curtain;
    if (m.includes('lock')) return DEVICE_ICON_SVGS.lock;
    if (m.includes('fridge') || m.includes('refrigerator')) return DEVICE_ICON_SVGS.fridge;
    if (m.includes('tv') || m.includes('television')) return DEVICE_ICON_SVGS.tv;
    if (m.includes('switch')) return DEVICE_ICON_SVGS.switch;
    if (m.includes('purifier')) return DEVICE_ICON_SVGS.purifier;
    return DEVICE_ICON_SVGS.unknown;
}

// 初始化
async function init() {
    console.log('🚀 初始化智能家居地图...');
    createTooltip();
    bindEvents();
    await loadHomes();
    startAutoRefresh();
}

// 创建设备悬停提示框
function createTooltip() {
    state.tooltip = document.createElement('div');
    state.tooltip.className = 'device-tooltip';
    document.body.appendChild(state.tooltip);
}

function bindEvents() {
    document.getElementById('homeSelect')?.addEventListener('change', onHomeChange);
    document.querySelectorAll('.scene-btn').forEach(btn => {
        btn.addEventListener('click', () => activateScene(btn.dataset.scene));
    });
    document.getElementById('editModeBtn')?.addEventListener('click', toggleEditMode);
    document.getElementById('generateBtn')?.addEventListener('click', showGeneratorModal);
    document.getElementById('saveBtn')?.addEventListener('click', async () => {
        await saveFloorPlan();
        // 手动点击保存后退出编辑模式
        if (state.editMode) toggleEditMode();
    });
    document.getElementById('resetViewBtn')?.addEventListener('click', resetView);
    document.getElementById('deviceFilter')?.addEventListener('change', renderDeviceList);
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.device-marker')) hideTooltip();
        hideContextMenu();
    });
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => { if (e.target === modal) closeAllModals(); });
    });
    const container = document.getElementById('floorPlanContainer');
    if (container) {
        container.addEventListener('dragover', handleDragOver);
        container.addEventListener('drop', handleDrop);
    }
}

function startAutoRefresh() {
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
    autoRefreshInterval = setInterval(async () => {
        if (state.currentHome && !state.editMode) await refreshDeviceStatus();
    }, AUTO_REFRESH_MS);
}

async function refreshDeviceStatus() {
    if (!state.currentHome) return;
    try {
        const response = await fetch(`/api/homes/${state.currentHome.home_id}/devices`);
        const data = await response.json();
        if (data.devices) {
            let hasChanges = false;
            data.devices.forEach(newDevice => {
                // 跳过已删除的设备
                if (state.deletedDeviceIds.has(newDevice.did)) return;

                const oldDevice = state.devices.find(d => d.did === newDevice.did);
                if (oldDevice) {
                    if (oldDevice.power !== newDevice.power || oldDevice.online !== newDevice.online) {
                        Object.assign(oldDevice, newDevice);
                        hasChanges = true;
                    }
                } else {
                    state.devices.push(newDevice);
                    hasChanges = true;
                }
            });
            if (hasChanges) {
                renderDeviceList();
                updateDeviceMarkers();
            }
        }
    } catch (error) {
        console.log('刷新失败:', error);
    }
}

async function loadHomes() {
    try {
        const response = await fetch('/api/homes');
        const data = await response.json();
        if (data.homes && data.homes.length > 0) {
            state.homes = data.homes;
        }
    } catch (error) {
        state.homes = [{ home_id: 'demo', home_name: '演示家庭', room_count: 0, device_count: 8 }];
    }
    updateHomeSelector();
}

function updateHomeSelector() {
    const select = document.getElementById('homeSelect');
    if (!select) return;
    select.innerHTML = '<option value="">选择家庭...</option>';
    state.homes.forEach(home => {
        const option = document.createElement('option');
        option.value = home.home_id;
        option.textContent = home.home_name;
        select.appendChild(option);
    });
    if (state.homes.length > 0) {
        select.value = state.homes[0].home_id;
        onHomeChange();
    }
}

async function onHomeChange() {
    const homeId = document.getElementById('homeSelect')?.value;
    if (!homeId) return;
    state.currentHome = state.homes.find(h => h.home_id === homeId);
    const homeNameEl = document.getElementById('homeName');
    if (homeNameEl) homeNameEl.textContent = state.currentHome?.home_name || '未命名';
    // 切换家庭时清空已删除设备记录
    state.deletedDeviceIds.clear();
    await loadFloorPlan(homeId);
    await loadDevices();
    renderFloorPlan();
    updateRoomCount();
}

async function loadFloorPlan(homeId) {
    try {
        const response = await fetch(`/api/homes/${homeId}/floorplan`);
        const data = await response.json();
        if (!data.error && data.rooms !== undefined) {
            state.floorPlan = data;
            return;
        }
    } catch (error) {}

    state.floorPlan = {
        home_id: homeId,
        home_name: state.currentHome?.home_name || '未命名',
        width: 800,
        height: 600,
        rooms: generateRoomLayout(2, 1, 1, 1, 1, 0),
        device_positions: {}
    };
}

async function loadDevices() {
    try {
        const response = await fetch(`/api/homes/${state.currentHome?.home_id}/devices`);
        const data = await response.json();
        if (data.devices && data.devices.length > 0) {
            // 过滤掉已删除的设备
            state.devices = data.devices.filter(d => !state.deletedDeviceIds.has(d.did));
        } else {
            state.devices = [];
        }
    } catch (error) {
        state.devices = [];
    }
    renderDeviceList();
    updateDeviceCount();
}

function generateRoomLayout(bedrooms, living, bathrooms, kitchen, balcony, study) {
    const rooms = [];
    const padding = 30;
    let currentY = padding;
    let roomId = 0;

    if (bedrooms > 0) {
        const w = (760 - padding * 2) / Math.min(bedrooms, 3);
        for (let i = 0; i < bedrooms; i++) {
            rooms.push({
                id: `room_${roomId++}`,
                type: 'bedroom',
                name: i === 0 ? '主卧' : `次卧${i}`,
                x: padding + (i % 3) * w,
                y: currentY + Math.floor(i / 3) * 160,
                width: w - padding,
                height: 140
            });
        }
        currentY += Math.ceil(bedrooms / 3) * 160 + padding;
    }

    if (living > 0) {
        rooms.push({
            id: `room_${roomId++}`, type: 'living', name: '客厅',
            x: padding, y: currentY, width: 380, height: 150
        });
        rooms.push({
            id: `room_${roomId++}`, type: 'living', name: '餐厅',
            x: padding + 400, y: currentY, width: 340, height: 150
        });
        currentY += 150 + padding;
    }

    let cx = padding;
    if (kitchen > 0) {
        rooms.push({ id: `room_${roomId++}`, type: 'kitchen', name: '厨房', x: cx, y: currentY, width: 150, height: 120 });
        cx += 170;
    }
    if (bathrooms > 0) {
        rooms.push({ id: `room_${roomId++}`, type: 'bathroom', name: '卫生间', x: cx, y: currentY, width: 100, height: 120 });
        cx += 120;
    }
    if (study > 0) {
        rooms.push({ id: `room_${roomId++}`, type: 'study', name: '书房', x: cx, y: currentY, width: 140, height: 120 });
    }
    if (balcony > 0) {
        rooms.push({ id: `room_${roomId++}`, type: 'balcony', name: '阳台', x: 600, y: currentY, width: 160, height: 120 });
    }

    rooms.unshift({ id: `room_${roomId++}`, type: 'entry', name: '玄关', x: 320, y: 5, width: 120, height: 50 });
    return rooms;
}

// 渲染2D俯视户型图
function renderFloorPlan() {
    const container = document.getElementById('floorPlanContainer');
    if (!container || !state.floorPlan) return;
    container.innerHTML = '';

    const planWidth = state.floorPlan.width || 800;
    const planHeight = state.floorPlan.height || 600;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'floor-plan-svg');
    svg.setAttribute('width', planWidth + 40);
    svg.setAttribute('height', planHeight + 40);
    svg.setAttribute('viewBox', `${-20} ${-20} ${planWidth + 40} ${planHeight + 40}`);

    // 定义渐变
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML = `
        <linearGradient id="deviceGradientOn" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#00ff88"/>
            <stop offset="100%" style="stop-color:#00d4ff"/>
        </linearGradient>
        <linearGradient id="deviceGradientOff" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#3a4a6a"/>
            <stop offset="100%" style="stop-color:#2a3a5a"/>
        </linearGradient>
    `;
    svg.appendChild(defs);

    // 先渲染房间和家具（背景层）
    if (state.floorPlan.rooms) {
        state.floorPlan.rooms.forEach(room => renderRoom(svg, room));
    }

    // 再渲染设备（上层）
    renderDevices(svg);

    container.appendChild(svg);
    state.svg = svg;
}

// 渲染房间和简笔画家具
function renderRoom(parent, room) {
    const config = ROOM_TYPES[room.type];
    const color = config?.color || 'rgba(100, 120, 160, 0.15)';

    const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    group.setAttribute('class', 'room-group');
    group.setAttribute('data-room-id', room.id);

    // 房间地板
    const floor = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    floor.setAttribute('class', 'room-floor');
    floor.setAttribute('x', room.x);
    floor.setAttribute('y', room.y);
    floor.setAttribute('width', room.width);
    floor.setAttribute('height', room.height);
    floor.setAttribute('fill', color);
    floor.setAttribute('rx', '4');

    // 房间边框
    const border = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    border.setAttribute('class', 'room-border');
    border.setAttribute('x', room.x);
    border.setAttribute('y', room.y);
    border.setAttribute('width', room.width);
    border.setAttribute('height', room.height);
    border.setAttribute('rx', '4');

    group.appendChild(floor);
    group.appendChild(border);

    // 添加简笔画家具
    renderSketchFurniture(group, room);

    // 房间名称
    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('class', 'room-label');
    label.setAttribute('x', room.x + room.width / 2);
    label.setAttribute('y', room.y + 18);
    label.textContent = room.name;
    group.appendChild(label);

    group.addEventListener('click', () => selectRoom(room));
    group.addEventListener('contextmenu', (e) => { if (state.editMode) showContextMenu(e, room); });
    if (state.editMode) group.addEventListener('mousedown', (e) => startRoomDrag(e, room));

    parent.appendChild(group);
}

// 渲染简笔画俯视图家具
function renderSketchFurniture(parent, room) {
    const furnitureGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    furnitureGroup.setAttribute('class', 'furniture-group');

    const cx = room.x + room.width / 2;
    const cy = room.y + room.height / 2;
    const left = room.x + 20;
    const right = room.x + room.width - 20;
    const top = room.y + 25;
    const bottom = room.y + room.height - 20;

    switch (room.type) {
        case 'bedroom':
            // 双人床靠下墙（床头在下方）
            const bed = FURNITURE_PATHS.bed(90, 65);
            const bedX = cx;
            const bedY = bottom - 35;
            addFurniturePath(furnitureGroup, bedX, bedY, bed, '#00D4FF', '0.5');
            // 左侧床头柜 - 床左侧靠墙
            const nsLeft = FURNITURE_PATHS.nightstand();
            addFurniturePath(furnitureGroup, bedX - 55, bedY + 20, nsLeft, '#00D4FF', '0.5');
            // 右侧床头柜 - 床右侧靠墙
            addFurniturePath(furnitureGroup, bedX + 55, bedY + 20, nsLeft, '#00D4FF', '0.5');
            break;

        case 'living':
            // 直排三人座沙发靠左墙，背部贴墙，面向电视
            const sofa = FURNITURE_PATHS.sofa3(140, 45);
            const sofaX = left + 80;  // 沙发离左墙一定距离
            const sofaY = cy;  // 垂直居中
            addFurniturePath(furnitureGroup, sofaX, sofaY, sofa, '#00D4FF', '0.5');
            // 茶几放在沙发前方中央（沙发和电视之间）
            const ct = FURNITURE_PATHS.coffeeTable();
            const tableX = cx + 20;  // 茶几在沙发前方偏右
            const tableY = sofaY;  // 与沙发同高
            addFurniturePath(furnitureGroup, tableX, tableY, ct, '#00D4FF', '0.5');
            // 电视柜靠右墙（与沙发对面）
            const tvStand = FURNITURE_PATHS.tvStand(80);
            const tvX = right - 45;
            const tvY = cy;
            addFurniturePath(furnitureGroup, tvX, tvY, tvStand, '#00D4FF', '0.5');
            break;

        case 'kitchen':
            // L型橱柜沿左墙和下墙
            const cabinet = FURNITURE_PATHS.cabinet(room.width - 50, room.height - 50);
            const cabX = cx - 10;
            const cabY = cy + 10;
            addFurniturePath(furnitureGroup, cabX, cabY, cabinet, '#FF6B35', '0.5');
            // 冰箱靠右上角
            const fridge = FURNITURE_PATHS.fridge();
            const fridgeX = right - 15;
            const fridgeY = top + 30;
            addFurniturePath(furnitureGroup, fridgeX, fridgeY, fridge, '#00D4FF', '0.5');
            break;

        case 'bathroom':
            // 马桶靠右下墙角
            const toilet = FURNITURE_PATHS.toilet();
            const toiletX = right - 20;
            const toiletY = bottom - 20;
            addFurniturePath(furnitureGroup, toiletX, toiletY, toilet, '#00D4FF', '0.5');
            // 洗手台靠右上墙角
            const sink = FURNITURE_PATHS.sink();
            const sinkX = right - 30;
            const sinkY = top + 25;
            addFurniturePath(furnitureGroup, sinkX, sinkY, sink, '#00D4FF', '0.5');
            // 淋浴区靠左下角
            const shower = FURNITURE_PATHS.shower();
            const showerX = left + 25;
            const showerY = bottom - 25;
            addFurniturePath(furnitureGroup, showerX, showerY, shower, '#00D4FF', '0.4');
            break;

        case 'study':
            // 书桌靠下墙
            const desk = FURNITURE_PATHS.desk();
            const deskX = cx;
            const deskY = bottom - 25;
            addFurniturePath(furnitureGroup, deskX, deskY, desk, '#00FF88', '0.5');
            // 书架靠右墙
            const shelf = FURNITURE_PATHS.bookshelf(80);
            const shelfX = right - 15;
            const shelfY = cy;
            addFurniturePath(furnitureGroup, shelfX, shelfY, shelf, '#00FF88', '0.5');
            break;

        case 'balcony':
            // 洗衣机靠左下角
            const washer = FURNITURE_PATHS.washer();
            const washerX = left + 25;
            const washerY = bottom - 30;
            addFurniturePath(furnitureGroup, washerX, washerY, washer, '#FFD700', '0.5');
            // 植物放右上角
            const plant = FURNITURE_PATHS.plant();
            const plantX = right - 20;
            const plantY = top + 20;
            addFurniturePath(furnitureGroup, plantX, plantY, plant, '#00D4FF', '0.5');
            break;

        case 'entry':
            // 鞋柜靠下墙
            const shoeCab = FURNITURE_PATHS.shoeCabinet(room.width - 30);
            const shoeX = cx;
            const shoeY = bottom - 10;
            addFurniturePath(furnitureGroup, shoeX, shoeY, shoeCab, '#00D4FF', '0.5');
            break;
    }

    parent.appendChild(furnitureGroup);
}

// 辅助函数：添加家具路径（支持对象形式的多部件家具）
function addFurniturePath(parent, x, y, pathData, strokeColor, opacity) {
    if (!pathData) return;

    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('transform', `translate(${x}, ${y})`);

    // 如果是对象，遍历所有属性
    if (typeof pathData === 'object' && pathData !== null) {
        Object.entries(pathData).forEach(([key, pathStr], index) => {
            if (!pathStr || typeof pathStr !== 'string') return;
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', pathStr);
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke', strokeColor);
            path.setAttribute('stroke-width', key === 'main' ? '2' : '1.5');
            path.setAttribute('opacity', key === 'main' ? opacity : '0.4');
            path.setAttribute('stroke-dasharray', key === 'main' ? '' : '3,2');
            g.appendChild(path);
        });
    } else if (typeof pathData === 'string') {
        // 向后兼容：字符串形式
        const paths = pathData.split(' M').filter(p => p.trim());
        paths.forEach((pathStr, index) => {
            const cleanPath = pathStr.startsWith('M') ? pathStr : 'M' + pathStr;
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', cleanPath);
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke', strokeColor);
            path.setAttribute('stroke-width', '1.5');
            path.setAttribute('opacity', index === 0 ? opacity : '0.4');
            path.setAttribute('stroke-dasharray', index === 0 ? '' : '3,2');
            g.appendChild(path);
        });
    }

    parent.appendChild(g);
}

// 渲染设备
function renderDevices(parent) {
    if (!state.devices || !state.floorPlan?.rooms) return;

    state.devices.forEach((device) => {
        // 只渲染有位置的设备（从地图上删除后不再自动显示）
        const pos = state.floorPlan.device_positions?.[device.did];
        if (!pos) return; // 没有位置的设备不显示

        renderDevice(parent, device, pos);
    });
}

// 渲染单个设备
function renderDevice(parent, device, pos) {
    const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    group.setAttribute('class', `device-marker ${device.power ? 'on' : 'off'}`);
    group.setAttribute('data-device-id', device.did);
    group.setAttribute('transform', `translate(${pos.x}, ${pos.y})`);
    group.style.cursor = 'pointer';

    // 设备背景圆
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('class', 'device-marker-circle');
    circle.setAttribute('r', '18');
    circle.setAttribute('cx', '0');
    circle.setAttribute('cy', '0');
    group.appendChild(circle);

    // 设备图标（SVG）
    const iconGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    iconGroup.innerHTML = getDeviceIconSvg(device.model);
    group.appendChild(iconGroup);

    // 设备名称
    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('class', 'device-marker-label');
    label.setAttribute('x', '0');
    label.setAttribute('y', '28');
    label.textContent = device.name?.substring(0, 6) + (device.name?.length > 6 ? '...' : '');
    group.appendChild(label);

    // 悬停事件（无抖动）
    group.addEventListener('mouseenter', (e) => showDeviceTooltip(e, device, pos));
    group.addEventListener('mouseleave', hideTooltip);
    group.addEventListener('click', (e) => { e.stopPropagation(); selectDevice(device); });

    // 编辑模式下的右键菜单
    if (state.editMode) {
        group.addEventListener('mousedown', (e) => startDeviceDrag(e, device));
        group.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            e.stopPropagation();
            showDeviceContextMenu(e, device);
        });
    }

    parent.appendChild(group);
}

// 显示设备悬停提示框 - 显示真实属性
function showDeviceTooltip(event, device, pos) {
    if (!state.tooltip) return;

    const iconSvg = getDeviceIconSvg(device.model);
    const statusText = device.online ? '在线' : '离线';
    const statusClass = device.online ? 'online' : 'offline';

    // 获取设备的真实属性
    let propertiesHtml = '';

    // 电源状态
    if (device.power !== undefined) {
        const powerText = device.power === true ? '开启' : '关闭';
        const powerColor = device.power === true ? 'var(--accent-green)' : 'var(--text-secondary)';
        propertiesHtml += `
            <div class="device-tooltip-row">
                <span class="device-tooltip-label">电源</span>
                <span class="device-tooltip-value" style="color:${powerColor}">${powerText}</span>
            </div>`;
    }

    // 亮度
    if (device.brightness !== undefined && device.brightness !== null) {
        const brightnessVal = typeof device.brightness === 'boolean' ?
            (device.brightness ? '开启' : '关闭') : `${device.brightness}%`;
        propertiesHtml += `
            <div class="device-tooltip-row">
                <span class="device-tooltip-label">亮度</span>
                <span class="device-tooltip-value">${brightnessVal}</span>
            </div>`;
    }

    // 温度
    if (device.temperature !== undefined && device.temperature !== null && typeof device.temperature !== 'boolean') {
        propertiesHtml += `
            <div class="device-tooltip-row">
                <span class="device-tooltip-label">温度</span>
                <span class="device-tooltip-value">${device.temperature}°C</span>
            </div>`;
    }

    // 目标温度（空调）
    if (device.target_temperature !== undefined && device.target_temperature !== null && typeof device.target_temperature !== 'boolean') {
        propertiesHtml += `
            <div class="device-tooltip-row">
                <span class="device-tooltip-label">目标温度</span>
                <span class="device-tooltip-value">${device.target_temperature}°C</span>
            </div>`;
    }

    // 湿度
    if (device.humidity !== undefined && device.humidity !== null) {
        propertiesHtml += `
            <div class="device-tooltip-row">
                <span class="device-tooltip-label">湿度</span>
                <span class="device-tooltip-value">${device.humidity}%</span>
            </div>`;
    }

    // 模式
    if (device.mode !== undefined && device.mode !== null && typeof device.mode !== 'boolean') {
        const modeNames = { 0: '自动', 1: '制冷', 2: '制热', 3: '除湿', 4: '送风' };
        const modeText = modeNames[device.mode] || device.mode;
        propertiesHtml += `
            <div class="device-tooltip-row">
                <span class="device-tooltip-label">模式</span>
                <span class="device-tooltip-value">${modeText}</span>
            </div>`;
    }

    // 音量
    if (device.volume !== undefined && device.volume !== null && typeof device.volume !== 'boolean') {
        propertiesHtml += `
            <div class="device-tooltip-row">
                <span class="device-tooltip-label">音量</span>
                <span class="device-tooltip-value">${device.volume}%</span>
            </div>`;
    }

    // 电池电量
    if (device.battery !== undefined && device.battery !== null) {
        const batteryText = typeof device.battery === 'number' ? `${device.battery}%` : device.battery;
        propertiesHtml += `
            <div class="device-tooltip-row">
                <span class="device-tooltip-label">电量</span>
                <span class="device-tooltip-value">${batteryText}</span>
            </div>`;
    }

    // 色温
    if (device.color_temperature !== undefined && device.color_temperature !== null) {
        propertiesHtml += `
            <div class="device-tooltip-row">
                <span class="device-tooltip-label">色温</span>
                <span class="device-tooltip-value">${device.color_temperature}K</span>
            </div>`;
    }

    state.tooltip.innerHTML = `
        <div class="device-tooltip-header">
            <div class="device-tooltip-icon">${iconSvg}</div>
            <div>
                <div class="device-tooltip-title">${device.name}</div>
                <span class="device-tooltip-status ${statusClass}">${statusText}</span>
            </div>
        </div>
        <div class="device-tooltip-content">
            <div class="device-tooltip-row">
                <span class="device-tooltip-label">型号</span>
                <span class="device-tooltip-value">${device.model || '未知'}</span>
            </div>
            <div class="device-tooltip-row">
                <span class="device-tooltip-label">设备ID</span>
                <span class="device-tooltip-value" style="font-size:10px;">${device.did}</span>
            </div>
            ${propertiesHtml}
        </div>
    `;

    // 计算位置
    const containerRect = document.getElementById('floorPlanContainer').getBoundingClientRect();
    const tooltipX = containerRect.left + pos.x + 25;
    const tooltipY = containerRect.top + pos.y - 50;

    state.tooltip.style.left = `${tooltipX}px`;
    state.tooltip.style.top = `${tooltipY}px`;
    state.tooltip.classList.add('show');
}

function hideTooltip() {
    if (state.tooltip) state.tooltip.classList.remove('show');
}

function updateDeviceMarkers() {
    if (!state.svg) return;
    state.devices.forEach(device => {
        const marker = state.svg.querySelector(`[data-device-id="${device.did}"]`);
        if (marker) marker.setAttribute('class', `device-marker ${device.power ? 'on' : 'off'}`);
    });
}

// 设备列表
function createDeviceListItem(device) {
    if (!device) return document.createElement('div');
    const div = document.createElement('div');
    div.className = 'device-item';
    div.draggable = true;
    div.dataset.deviceId = device.did;
    if (state.floorPlan?.device_positions?.[device.did]) div.classList.add('placed');
    if (device.power === true) div.classList.add('active');

    const isOnline = device.online;
    const isOn = device.power === true;
    const statusClass = isOnline ? (isOn ? 'online active' : 'online') : 'offline';
    const statusText = isOnline ? (isOn ? 'ON' : 'OFF') : '离线';

    // 使用与户型图相同的SVG图标
    const iconSvg = getDeviceIconSvg(device.model);

    div.innerHTML = `
        <div class="device-status ${statusClass}"></div>
        <div class="device-icon" style="background: var(--bg-dark); border: 1px solid var(--border-color); display: flex; align-items: center; justify-content: center; overflow: hidden;">
            <svg width="32" height="32" viewBox="-25 -25 50 50" style="display: block;">${iconSvg}</svg>
        </div>
        <div class="device-info">
            <div class="device-name">${device.name || '未命名'}</div>
            <div class="device-status">${statusText}</div>
        </div>
    `;
    div.addEventListener('click', () => selectDevice(device));
    div.addEventListener('dragstart', (e) => handleDeviceDragStart(e, device));
    return div;
}

function renderDeviceList() {
    const container = document.getElementById('deviceList');
    if (!container) return;
    const filter = document.getElementById('deviceFilter')?.value || 'all';
    container.innerHTML = '';

    if (!state.devices || state.devices.length === 0) {
        container.innerHTML = '<div class="loading">暂无设备</div>';
        return;
    }

    const filtered = filter === 'all' ? state.devices : state.devices.filter(d => d.model?.toLowerCase().includes(filter));
    filtered.forEach(device => container.appendChild(createDeviceListItem(device)));
}

function handleDeviceDragStart(e, device) {
    e.dataTransfer.setData('deviceId', device.did);
    e.target.classList.add('dragging');
}

function handleDragOver(e) { e.preventDefault(); }

async function handleDrop(e) {
    e.preventDefault();
    const deviceId = e.dataTransfer.getData('deviceId');
    if (!deviceId || !state.floorPlan) return;
    const rect = document.getElementById('floorPlanContainer').getBoundingClientRect();
    if (!state.floorPlan.device_positions) state.floorPlan.device_positions = {};
    state.floorPlan.device_positions[deviceId] = { x: e.clientX - rect.left - 20, y: e.clientY - rect.top - 20 };
    renderFloorPlan();
    renderDeviceList();

    // 自动保存设备位置
    await saveFloorPlan();
}

// 拖拽功能
function startRoomDrag(e, room) {
    if (!state.editMode) return;
    e.preventDefault();
    state.draggedRoom = room;
    state.dragOffset.x = e.clientX - room.x;
    state.dragOffset.y = e.clientY - room.y;
    document.addEventListener('mousemove', handleRoomDrag);
    document.addEventListener('mouseup', stopRoomDrag);
}

function handleRoomDrag(e) {
    if (!state.draggedRoom) return;
    state.draggedRoom.x = e.clientX - state.dragOffset.x;
    state.draggedRoom.y = e.clientY - state.dragOffset.y;
    renderFloorPlan();
}

function stopRoomDrag() {
    state.draggedRoom = null;
    document.removeEventListener('mousemove', handleRoomDrag);
    document.removeEventListener('mouseup', stopRoomDrag);
}

function startDeviceDrag(e, device) {
    if (!state.editMode) return;
    e.preventDefault();
    state.draggedDevice = device;
    const pos = state.floorPlan?.device_positions?.[device.did] || { x: 0, y: 0 };
    state.dragOffset.x = e.clientX - pos.x;
    state.dragOffset.y = e.clientY - pos.y;
    document.addEventListener('mousemove', handleDeviceDrag);
    document.addEventListener('mouseup', stopDeviceDrag);
}

function handleDeviceDrag(e) {
    if (!state.draggedDevice) return;
    if (!state.floorPlan.device_positions) state.floorPlan.device_positions = {};
    state.floorPlan.device_positions[state.draggedDevice.did] = { x: e.clientX - state.dragOffset.x, y: e.clientY - state.dragOffset.y };
    renderFloorPlan();
}

async function stopDeviceDrag() {
    state.draggedDevice = null;
    document.removeEventListener('mousemove', handleDeviceDrag);
    document.removeEventListener('mouseup', stopDeviceDrag);

    // 拖拽结束后自动保存位置
    await saveFloorPlan();
}

// 选择和编辑
function selectDevice(device) {
    state.selectedDevice = device;
    showDeviceProperties(device);
}

function showDeviceProperties(device) {
    const container = document.getElementById('deviceProperties');
    if (!container) return;

    const iconChar = device.model?.toLowerCase().includes('light') ? '💡' :
                     device.model?.toLowerCase().includes('ac') ? '❄️' :
                     device.model?.toLowerCase().includes('camera') ? '📷' : '📟';
    const statusClass = device.online ? 'online' : 'offline';
    const statusText = device.online ? '在线' : '离线';

    let controls = '';
    if (device.model?.toLowerCase().includes('light')) {
        controls = `<div class="property-group"><h4>控制</h4><div class="property-item"><span>电源</span><div class="toggle-switch ${device.power ? 'on' : ''}" onclick="toggleDevice('${device.did}')"></div></div></div>`;
    }

    container.innerHTML = `
        <div class="device-detail">
            <div class="device-detail-header">
                <div class="device-detail-icon">${iconChar}</div>
                <div class="device-detail-info">
                    <h4>${device.name}</h4>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
            </div>
            ${controls}
        </div>
    `;
}

async function toggleDevice(deviceId) {
    const device = state.devices.find(d => d.did === deviceId);
    if (!device) return;
    try {
        await fetch(`/api/devices/${deviceId}/control`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: device.power ? 'turn_off' : 'turn_on' })
        });
    } catch (e) {}
    device.power = !device.power;
    updateDeviceMarkers();
    renderDeviceList();
    showDeviceProperties(device);
}

function selectRoom(room) {
    state.selectedRoom = room;
    if (state.editMode) highlightRoom(room.id);
}

function highlightRoom(roomId) {
    document.querySelectorAll('.room-group').forEach(el => {
        el.style.filter = el.dataset.roomId === roomId ? 'brightness(1.05)' : 'none';
    });
}

// 右键菜单
function showContextMenu(e, room) {
    e.preventDefault();
    state.selectedRoom = room;
    const menu = document.getElementById('contextMenu');
    if (menu) {
        menu.style.left = e.pageX + 'px';
        menu.style.top = e.pageY + 'px';
        menu.classList.add('show');
    }
}

function hideContextMenu() {
    const menu = document.getElementById('contextMenu');
    if (menu) menu.classList.remove('show');
    // 同时隐藏设备右键菜单
    const deviceMenu = document.getElementById('deviceContextMenu');
    if (deviceMenu) deviceMenu.classList.remove('show');
}

function editRoom() {
    hideContextMenu();
    if (!state.selectedRoom) return;
    document.getElementById('roomNameInput').value = state.selectedRoom.name;
    document.getElementById('roomWidthInput').value = Math.round(state.selectedRoom.width);
    document.getElementById('roomHeightInput').value = Math.round(state.selectedRoom.height);
    document.getElementById('roomEditModal').classList.add('show');
}

function closeRoomEditModal() {
    document.getElementById('roomEditModal')?.classList.remove('show');
}

function saveRoomEdit() {
    if (!state.selectedRoom) return;
    const name = document.getElementById('roomNameInput').value;
    const w = parseInt(document.getElementById('roomWidthInput').value);
    const h = parseInt(document.getElementById('roomHeightInput').value);
    if (name) state.selectedRoom.name = name;
    if (w > 50) state.selectedRoom.width = w;
    if (h > 50) state.selectedRoom.height = h;
    closeRoomEditModal();
    renderFloorPlan();
}

function deleteRoom() {
    hideContextMenu();
    if (!state.selectedRoom || !state.floorPlan) return;
    if (!confirm(`删除房间 "${state.selectedRoom.name}"?`)) return;
    state.floorPlan.rooms = state.floorPlan.rooms.filter(r => r.id !== state.selectedRoom.id);
    state.selectedRoom = null;
    closeRoomEditModal();
    renderFloorPlan();
    updateRoomCount();
}

function deleteRoomFromMenu() { deleteRoom(); }

// 显示设备右键菜单
function showDeviceContextMenu(e, device) {
    state.selectedDevice = device;
    const menu = document.getElementById('deviceContextMenu');
    if (menu) {
        menu.style.left = e.pageX + 'px';
        menu.style.top = e.pageY + 'px';
        menu.classList.add('show');
    }
}

// 删除设备
async function deleteDeviceFromMenu() {
    hideContextMenu();
    if (!state.selectedDevice) return;
    if (!confirm(`将设备 "${state.selectedDevice.name}" 从地图上移除?`)) return;

    const deviceId = state.selectedDevice.did;

    // 从户型图中移除设备位置（设备仍在列表中，只是不在地图上显示）
    if (state.floorPlan && state.floorPlan.device_positions) {
        delete state.floorPlan.device_positions[deviceId];
    }

    state.selectedDevice = null;
    renderFloorPlan();

    // 自动保存户型图
    await saveFloorPlan();
}

function toggleEditMode() {
    state.editMode = !state.editMode;
    const btn = document.getElementById('editModeBtn');
    const saveBtn = document.getElementById('saveBtn');
    if (state.editMode) {
        btn.textContent = '✓ 完成';
        btn.classList.add('btn-success');
        saveBtn.style.display = 'inline-flex';
    } else {
        btn.textContent = '✏️ 编辑';
        btn.classList.remove('btn-success');
        saveBtn.style.display = 'none';
        hideContextMenu();
    }
    renderFloorPlan();
}

async function saveFloorPlan() {
    if (!state.floorPlan || !state.currentHome) return;
    try {
        await fetch(`/api/homes/${state.currentHome.home_id}/floorplan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state.floorPlan)
        });
    } catch (e) {}
    // 不再自动退出编辑模式，让用户手动点击"完成"按钮
}

function showGeneratorModal() {
    document.getElementById('generatorModal')?.classList.add('show');
}

function closeGeneratorModal() {
    document.getElementById('generatorModal')?.classList.remove('show');
}

function generateFloorPlan() {
    const b = parseInt(document.getElementById('bedroomCount')?.value) || 2;
    const l = parseInt(document.getElementById('livingCount')?.value) || 1;
    const ba = parseInt(document.getElementById('bathroomCount')?.value) || 1;
    const k = parseInt(document.getElementById('kitchenCount')?.value) || 1;
    const bl = parseInt(document.getElementById('balconyCount')?.value) || 1;
    const s = parseInt(document.getElementById('studyCount')?.value) || 0;

    state.floorPlan = {
        home_id: state.currentHome?.home_id || 'demo',
        home_name: state.currentHome?.home_name || '未命名',
        width: 800, height: 600,
        rooms: generateRoomLayout(b, l, ba, k, bl, s),
        device_positions: {}
    };
    closeGeneratorModal();
    renderFloorPlan();
    updateRoomCount();
    if (!state.editMode) toggleEditMode();
}

function resetView() {
    renderFloorPlan();
}

function activateScene(scene) {
    document.querySelectorAll('.scene-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-scene="${scene}"]`)?.classList.add('active');
}

function updateRoomCount() {
    const el = document.getElementById('roomCount');
    if (el) el.textContent = `${state.floorPlan?.rooms?.length || 0} 个房间`;
}

function updateDeviceCount() {
    const online = state.devices.filter(d => d.online).length;
    const onlineEl = document.getElementById('onlineCount');
    const totalEl = document.getElementById('totalCount');
    if (onlineEl) onlineEl.textContent = `在线: ${online}`;
    if (totalEl) totalEl.textContent = `总计: ${state.devices.length}`;
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('show'));
}

document.addEventListener('DOMContentLoaded', init);

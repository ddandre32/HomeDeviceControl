/**
 * 智能家居地图应用 - 深色主题版本
 * 支持户型自动生成和拖拽编辑
 */

// 全局状态
const state = {
    homes: [],
    currentHome: null,
    devices: [],
    floorPlan: null,
    editMode: false,
    selectedDevice: null,
    selectedRoom: null,
    draggedRoom: null,
    resizedRoom: null,
    draggedDevice: null,  // 添加：正在拖拽的设备
    deviceDragOffset: { x: 0, y: 0 },  // 添加：设备拖拽偏移量
    dragOffset: { x: 0, y: 0 },
    svgScale: 1,
    svgOffset: { x: 0, y: 0 }
};

// 节流控制变量
let resizeThrottleId = null;
let dragThrottleId = null;
let lastResizeTime = 0;
let lastDragTime = 0;
const THROTTLE_MS = 16; // 约60fps

// 自动刷新定时器
let autoRefreshInterval = null;
const AUTO_REFRESH_MS = 3000; // 每3秒刷新一次

// 房间类型配置
const ROOM_TYPES = {
    bedroom: { name: '卧室', color: '#1a2744', icon: '🛏️', minSize: { w: 120, h: 100 } },
    living: { name: '客厅', color: '#1a2f44', icon: '🛋️', minSize: { w: 180, h: 140 } },
    bathroom: { name: '卫生间', color: '#1a2438', icon: '🚿', minSize: { w: 80, h: 80 } },
    kitchen: { name: '厨房', color: '#1a2a3d', icon: '🍳', minSize: { w: 100, h: 100 } },
    balcony: { name: '阳台', color: '#1a2235', icon: '🌿', minSize: { w: 100, h: 60 } },
    study: { name: '书房', color: '#1a263a', icon: '📚', minSize: { w: 100, h: 90 } },
    entry: { name: '玄关', color: '#1a202e', icon: '🚪', minSize: { w: 80, h: 80 } }
};

// 设备图标映射
const DEVICE_ICONS = {
    'light': '💡',
    'lamp': '💡',
    'switch': '🔘',
    'curtain': '🪟',
    'air_conditioner': '❄️',
    'purifier': '🌬️',
    'speaker': '🔊',
    'camera': '📷',
    'lock': '🔒',
    'fridge': '🧊',
    'tv': '📺',
    'unknown': '📟'
};

// 初始化
async function init() {
    console.log('🚀 初始化智能家居地图...');
    bindEvents();
    await loadHomes();
    initSVGInteractions();
    startAutoRefresh();
}

// 启动自动刷新
function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    autoRefreshInterval = setInterval(async () => {
        if (state.currentHome && !state.editMode) {
            await refreshDeviceStatus();
        }
    }, AUTO_REFRESH_MS);
}

// 停止自动刷新
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// 刷新设备状态 - 只更新状态不重新渲染整个视图
async function refreshDeviceStatus() {
    if (!state.currentHome) return;

    try {
        const response = await fetch(`/api/homes/${state.currentHome.home_id}/devices`);
        const data = await response.json();

        if (data.devices) {
            // 更新设备状态数据
            let hasChanges = false;
            data.devices.forEach(newDevice => {
                const oldDevice = state.devices.find(d => d.did === newDevice.did);
                if (oldDevice) {
                    // 检查是否有状态变化
                    if (oldDevice.power !== newDevice.power ||
                        oldDevice.online !== newDevice.online ||
                        oldDevice.brightness !== newDevice.brightness) {
                        hasChanges = true;
                        // 更新设备数据
                        Object.assign(oldDevice, newDevice);
                        // 更新UI
                        updateDeviceUI(oldDevice);
                    }
                } else {
                    // 新设备
                    state.devices.push(newDevice);
                    hasChanges = true;
                }
            });

            if (hasChanges) {
                renderDeviceList();
                updateDeviceCount();
            }
        }
    } catch (error) {
        console.log('刷新设备状态失败:', error);
    }
}

// 更新单个设备的UI（不重新渲染整个户型图）
function updateDeviceUI(device) {
    // 更新设备列表中的状态
    const deviceItem = document.querySelector(`.device-item[data-device-id="${device.did}"]`);
    if (deviceItem) {
        // 更新状态指示器
        const statusEl = deviceItem.querySelector('.device-status');
        const infoEl = deviceItem.querySelector('.device-info');

        // 清除旧的状态类
        deviceItem.classList.remove('active');
        if (statusEl) {
            statusEl.className = 'device-status';
        }

        // 设置新状态
        if (device.online) {
            if (device.power === true) {
                statusEl?.classList.add('online', 'active');
                deviceItem.classList.add('active');
                if (infoEl) infoEl.textContent = '开启';
            } else {
                statusEl?.classList.add('online');
                if (infoEl) infoEl.textContent = '关闭';
            }
        } else {
            statusEl?.classList.add('offline');
            if (infoEl) infoEl.textContent = '离线';
        }
    }

    // 更新SVG中的设备状态
    const deviceNode = document.querySelector(`.device-node[data-device-id="${device.did}"]`);
    if (deviceNode) {
        const circle = deviceNode.querySelector('.device-circle');
        if (circle) {
            // 移除旧的状态类
            circle.classList.remove('on', 'off', 'offline');

            // 添加新的状态类
            if (!device.online) {
                circle.classList.add('offline');
            } else if (device.power === true) {
                circle.classList.add('on');
            } else {
                circle.classList.add('off');
            }
        }
    }
}

// 绑定事件
function bindEvents() {
    // 家庭选择
    document.getElementById('homeSelect').addEventListener('change', onHomeChange);

    // 场景按钮
    document.querySelectorAll('.scene-btn').forEach(btn => {
        btn.addEventListener('click', () => activateScene(btn.dataset.scene));
    });

    // 编辑模式
    document.getElementById('editModeBtn').addEventListener('click', toggleEditMode);

    // 生成户型
    document.getElementById('generateBtn').addEventListener('click', showGeneratorModal);

    // 保存
    document.getElementById('saveBtn').addEventListener('click', saveFloorPlan);

    // 视图控制
    document.getElementById('zoomInBtn').addEventListener('click', () => zoomView(0.1));
    document.getElementById('zoomOutBtn').addEventListener('click', () => zoomView(-0.1));
    document.getElementById('resetViewBtn').addEventListener('click', resetView);

    // 设备筛选
    document.getElementById('deviceFilter').addEventListener('change', renderDeviceList);

    // 右键菜单
    document.addEventListener('click', hideContextMenu);

    // 模态框关闭
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeAllModals();
        });
    });
}

// 加载家庭列表 - 修复：确保始终有数据
async function loadHomes() {
    let homesLoaded = false;

    try {
        const response = await fetch('/api/homes');
        const data = await response.json();

        if (data.homes && data.homes.length > 0) {
            state.homes = data.homes;
            homesLoaded = true;
        }
    } catch (error) {
        console.log('API加载失败:', error);
    }

    // 如果没有从API获取到家庭，创建演示家庭
    if (!homesLoaded || state.homes.length === 0) {
        console.log('使用演示模式...');
        state.homes = [{
            home_id: 'demo',
            home_name: '我的家（演示模式）',
            room_count: 0,
            device_count: 8
        }];
    }

    updateHomeSelector();
}

// 更新家庭选择器
function updateHomeSelector() {
    const select = document.getElementById('homeSelect');
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

// 家庭切换
async function onHomeChange() {
    const homeId = document.getElementById('homeSelect').value;
    if (!homeId) return;

    state.currentHome = state.homes.find(h => h.home_id === homeId);
    document.getElementById('homeName').textContent = state.currentHome?.home_name || '未命名';

    // 加载户型图
    await loadFloorPlan(homeId);

    // 加载设备
    await loadDevices();

    // 渲染
    renderFloorPlan();
    updateRoomCount();
}

// 加载户型图 - 修复：正确处理空户型图
async function loadFloorPlan(homeId) {
    let planLoaded = false;

    try {
        const response = await fetch(`/api/homes/${homeId}/floorplan`);
        const data = await response.json();

        // 修复：只要 rooms 字段存在（即使是空数组）就认为加载成功
        // 用户可能有意删除所有房间，只保留设备位置
        if (!data.error && data.rooms !== undefined && data.rooms !== null) {
            state.floorPlan = data;
            planLoaded = true;
            console.log('户型图加载成功:', data.rooms.length, '个房间,', Object.keys(data.device_positions || {}).length, '个设备位置');
        }
    } catch (error) {
        console.log('户型图API加载失败:', error);
    }

    // 如果没有户型图（API返回错误或rooms字段不存在），创建默认户型
    if (!planLoaded) {
        console.log('创建默认户型图...');
        state.floorPlan = {
            home_id: homeId,
            home_name: state.currentHome?.home_name || '未命名',
            width: 900,
            height: 600,
            rooms: [],
            device_positions: {}
        };

        // 自动生成一个默认户型
        state.floorPlan.rooms = generateRoomLayout(2, 1, 1, 1, 1, 0);
    }
}

// 加载设备 - 修复：确保始终有数据
async function loadDevices() {
    let devicesLoaded = false;

    try {
        const response = await fetch(`/api/homes/${state.currentHome?.home_id}/devices`);
        const data = await response.json();

        if (data.devices && data.devices.length > 0) {
            state.devices = data.devices;
            devicesLoaded = true;
        }
    } catch (error) {
        console.log('API加载失败，使用演示数据:', error);
    }

    // 如果没有从API获取到设备，生成演示数据
    if (!devicesLoaded || state.devices.length === 0) {
        console.log('生成演示设备数据...');
        state.devices = generateDemoDevices();
    }

    renderDeviceList();
    updateDeviceCount();
}

// 生成演示设备
function generateDemoDevices() {
    const devices = [];
    const types = ['light', 'light', 'light', 'ac', 'speaker', 'curtain', 'camera', 'lock'];
    const names = ['客厅主灯', '卧室灯', '餐厅灯', '客厅空调', '智能音箱', '智能窗帘', '门口摄像头', '智能门锁'];

    types.forEach((type, i) => {
        devices.push({
            did: `device_${i}`,
            name: names[i],
            model: type,
            online: Math.random() > 0.2,
            home_id: state.currentHome?.home_id,
            room_id: null
        });
    });
    return devices;
}

// 显示户型生成器对话框
function showGeneratorModal() {
    document.getElementById('generatorModal').classList.add('show');
}

// 关闭户型生成器
function closeGeneratorModal() {
    document.getElementById('generatorModal').classList.remove('show');
}

// 生成户型图
function generateFloorPlan() {
    const bedrooms = parseInt(document.getElementById('bedroomCount').value) || 2;
    const living = parseInt(document.getElementById('livingCount').value) || 1;
    const bathrooms = parseInt(document.getElementById('bathroomCount').value) || 1;
    const kitchen = parseInt(document.getElementById('kitchenCount').value) || 1;
    const balcony = parseInt(document.getElementById('balconyCount').value) || 1;
    const study = parseInt(document.getElementById('studyCount').value) || 0;

    // 生成房间布局
    const rooms = generateRoomLayout(bedrooms, living, bathrooms, kitchen, balcony, study);

    state.floorPlan = {
        home_id: state.currentHome?.home_id || 'demo',
        home_name: state.currentHome?.home_name || '未命名',
        width: 900,
        height: 600,
        rooms: rooms,
        device_positions: {}
    };

    closeGeneratorModal();
    renderFloorPlan();
    updateRoomCount();

    // 自动进入编辑模式
    if (!state.editMode) {
        toggleEditMode();
    }
}

// 生成房间布局算法
function generateRoomLayout(bedrooms, living, bathrooms, kitchen, balcony, study) {
    const rooms = [];
    const padding = 10;
    let currentY = padding;
    let roomId = 0;

    // 上半部分：卧室区域
    if (bedrooms > 0) {
        const bedroomWidth = (900 - padding * 2) / Math.min(bedrooms, 3);
        const bedroomHeight = 180;

        for (let i = 0; i < bedrooms; i++) {
            const col = i % 3;
            const row = Math.floor(i / 3);

            rooms.push({
                id: `room_${roomId++}`,
                type: 'bedroom',
                name: i === 0 ? '主卧' : `次卧${i}`,
                x: padding + col * bedroomWidth,
                y: currentY + row * (bedroomHeight + padding),
                width: bedroomWidth - padding,
                height: bedroomHeight,
                color: ROOM_TYPES.bedroom.color
            });
        }
        currentY += Math.ceil(bedrooms / 3) * (bedroomHeight + padding) + padding;
    }

    // 中间：客厅 + 餐厅
    if (living > 0) {
        const livingWidth = 400;
        rooms.push({
            id: `room_${roomId++}`,
            type: 'living',
            name: '客厅',
            x: padding,
            y: currentY,
            width: livingWidth,
            height: 200,
            color: ROOM_TYPES.living.color
        });

        // 餐厅
        rooms.push({
            id: `room_${roomId++}`,
            type: 'living',
            name: '餐厅',
            x: padding + livingWidth + padding,
            y: currentY,
            width: 900 - livingWidth - padding * 3,
            height: 200,
            color: ROOM_TYPES.living.color
        });

        currentY += 200 + padding;
    }

    // 厨房
    if (kitchen > 0) {
        rooms.push({
            id: `room_${roomId++}`,
            type: 'kitchen',
            name: '厨房',
            x: padding,
            y: currentY,
            width: 200,
            height: 150,
            color: ROOM_TYPES.kitchen.color
        });
    }

    // 卫生间
    if (bathrooms > 0) {
        for (let i = 0; i < bathrooms; i++) {
            rooms.push({
                id: `room_${roomId++}`,
                type: 'bathroom',
                name: i === 0 ? '卫生间' : `卫生间${i + 1}`,
                x: 220 + i * 130,
                y: currentY,
                width: 120,
                height: 150,
                color: ROOM_TYPES.bathroom.color
            });
        }
    }

    // 书房
    if (study > 0) {
        rooms.push({
            id: `room_${roomId++}`,
            type: 'study',
            name: '书房',
            x: 220 + bathrooms * 130 + padding,
            y: currentY,
            width: 180,
            height: 150,
            color: ROOM_TYPES.study.color
        });
    }

    // 阳台（放在最下方或最右侧）
    if (balcony > 0) {
        rooms.push({
            id: `room_${roomId++}`,
            type: 'balcony',
            name: '阳台',
            x: 700,
            y: currentY,
            width: 190,
            height: 150,
            color: ROOM_TYPES.balcony.color
        });
    }

    // 玄关
    rooms.unshift({
        id: `room_${roomId++}`,
        type: 'entry',
        name: '玄关',
        x: 350,
        y: 10,
        width: 150,
        height: 80,
        color: ROOM_TYPES.entry.color
    });

    return rooms;
}

// 渲染户型图（SVG）
function renderFloorPlan() {
    const roomsLayer = document.getElementById('roomsLayer');
    const furnitureLayer = document.getElementById('furnitureLayer');
    const devicesLayer = document.getElementById('devicesLayer');
    const overlayLayer = document.getElementById('overlayLayer');

    // 清空所有层
    roomsLayer.innerHTML = '';
    furnitureLayer.innerHTML = '';
    devicesLayer.innerHTML = '';
    overlayLayer.innerHTML = '';

    if (!state.floorPlan) return;

    // 首先移除可能存在的编辑模式指示器
    const existingIndicator = document.querySelector('.edit-indicator');
    if (existingIndicator) existingIndicator.remove();

    // 添加编辑模式指示器
    if (state.editMode) {
        const indicator = document.createElement('div');
        indicator.className = 'edit-indicator';
        indicator.textContent = '📐 编辑模式：拖拽房间移动，拖拽右下角调整大小';
        document.querySelector('.floor-plan-wrapper').appendChild(indicator);
    }

    // 如果没有房间但有设备位置，显示提示信息
    const hasRooms = state.floorPlan.rooms && state.floorPlan.rooms.length > 0;
    const hasDevicePositions = state.floorPlan.device_positions && Object.keys(state.floorPlan.device_positions).length > 0;

    if (!hasRooms && hasDevicePositions) {
        // 显示提示：有设备位置但没有房间
        const hintLayer = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        hintLayer.setAttribute('x', 450);
        hintLayer.setAttribute('y', 300);
        hintLayer.setAttribute('text-anchor', 'middle');
        hintLayer.setAttribute('fill', '#6a85a8');
        hintLayer.setAttribute('font-size', '16');
        hintLayer.textContent = '户型图没有房间，点击"生成户型"创建房间，或进入编辑模式添加房间';
        roomsLayer.appendChild(hintLayer);
    }

    // 渲染房间（如果有）
    if (state.floorPlan.rooms) {
        state.floorPlan.rooms.forEach(room => {
            renderRoom(room, roomsLayer, furnitureLayer, overlayLayer);
        });
    }

    // 渲染设备
    renderDevices(devicesLayer);
}

// 渲染单个房间
function renderRoom(room, roomsLayer, furnitureLayer, overlayLayer) {
    const roomGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    roomGroup.setAttribute('class', 'room-group');
    roomGroup.setAttribute('data-room-id', room.id);

    // 房间矩形
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('class', state.editMode ? 'room-rect editing' : 'room-rect');
    rect.setAttribute('x', room.x);
    rect.setAttribute('y', room.y);
    rect.setAttribute('width', room.width);
    rect.setAttribute('height', room.height);
    rect.setAttribute('rx', 4);
    rect.setAttribute('fill', room.color || ROOM_TYPES[room.type]?.color || '#1a2744');
    rect.setAttribute('stroke', state.selectedRoom?.id === room.id ? '#3b82f6' : '#2a3d58');
    rect.setAttribute('stroke-width', state.selectedRoom?.id === room.id ? '3' : '2');
    rect.setAttribute('id', `room-rect-${room.id}`);

    // 事件绑定
    if (state.editMode) {
        rect.addEventListener('mousedown', (e) => startDragRoom(e, room));
        rect.addEventListener('contextmenu', (e) => showContextMenu(e, room));
    }

    roomGroup.appendChild(rect);

    // 房间标签
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('class', 'room-label room-label-main');
    text.setAttribute('x', room.x + room.width / 2);
    text.setAttribute('y', room.y + room.height / 2);
    text.textContent = room.name;
    roomGroup.appendChild(text);

    // 允许设备拖拽放置到房间（始终启用，不仅限于编辑模式）
    roomGroup.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    });
    roomGroup.addEventListener('drop', (e) => handleDeviceDropOnRoom(e, room));

    // 编辑模式下的拖拽手柄和调整大小手柄
    if (state.editMode) {
        // 拖拽手柄（中心点）
        const dragHandle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        dragHandle.setAttribute('class', 'drag-handle');
        dragHandle.setAttribute('cx', room.x + room.width / 2);
        dragHandle.setAttribute('cy', room.y + room.height / 2);
        dragHandle.setAttribute('r', 6);
        dragHandle.setAttribute('id', `drag-handle-${room.id}`);
        dragHandle.addEventListener('mousedown', (e) => startDragRoom(e, room));
        overlayLayer.appendChild(dragHandle);

        // 调整大小手柄（右下角）
        const resizeHandle = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        resizeHandle.setAttribute('class', 'resize-handle');
        resizeHandle.setAttribute('x', room.x + room.width - 10);
        resizeHandle.setAttribute('y', room.y + room.height - 10);
        resizeHandle.setAttribute('width', 16);
        resizeHandle.setAttribute('height', 16);
        resizeHandle.setAttribute('rx', 3);
        resizeHandle.setAttribute('id', `resize-handle-${room.id}`);
        resizeHandle.addEventListener('mousedown', (e) => startResizeRoom(e, room));
        overlayLayer.appendChild(resizeHandle);
    }

    roomsLayer.appendChild(roomGroup);

    // 渲染家具
    renderFurniture(room, furnitureLayer);
}

// 渲染家具
function renderFurniture(room, layer) {
    // 根据房间类型渲染不同的家具轮廓
    const furnitureGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    furnitureGroup.setAttribute('class', 'furniture-group');
    furnitureGroup.setAttribute('opacity', '0.4');

    const cx = room.x + room.width / 2;
    const cy = room.y + room.height / 2;

    switch (room.type) {
        case 'bedroom':
            // 床
            const bed = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bed.setAttribute('class', 'furniture');
            bed.setAttribute('x', cx - 40);
            bed.setAttribute('y', cy - 10);
            bed.setAttribute('width', 80);
            bed.setAttribute('height', 50);
            bed.setAttribute('rx', 4);
            furnitureGroup.appendChild(bed);
            break;

        case 'living':
            // 沙发
            const sofa = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            sofa.setAttribute('class', 'furniture');
            sofa.setAttribute('x', cx - 60);
            sofa.setAttribute('y', cy + 10);
            sofa.setAttribute('width', 120);
            sofa.setAttribute('height', 40);
            sofa.setAttribute('rx', 6);
            furnitureGroup.appendChild(sofa);
            break;

        case 'kitchen':
            // 橱柜
            const counter = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            counter.setAttribute('class', 'furniture');
            counter.setAttribute('x', room.x + 10);
            counter.setAttribute('y', room.y + 10);
            counter.setAttribute('width', room.width - 20);
            counter.setAttribute('height', 30);
            counter.setAttribute('rx', 3);
            furnitureGroup.appendChild(counter);
            break;

        case 'bathroom':
            // 马桶和洗手池
            const toilet = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            toilet.setAttribute('class', 'furniture');
            toilet.setAttribute('cx', room.x + room.width - 25);
            toilet.setAttribute('cy', room.y + 25);
            toilet.setAttribute('r', 12);
            furnitureGroup.appendChild(toilet);
            break;
    }

    layer.appendChild(furnitureGroup);
}

// 渲染设备
function renderDevices(layer) {
    // 移除旧的弹窗
    const oldTooltip = document.getElementById('deviceTooltip');
    if (oldTooltip) oldTooltip.remove();

    // 创建全局弹窗元素
    createDeviceTooltip();

    state.devices.forEach(device => {
        // 获取设备位置
        let pos = state.floorPlan.device_positions?.[device.did];
        if (!pos) {
            // 默认位置：在对应房间的随机位置
            const room = state.floorPlan.rooms.find(r => r.id === device.room_id);
            if (room) {
                pos = {
                    x: room.x + room.width / 2,
                    y: room.y + room.height / 2
                };
            }
        }

        if (!pos) return;

        const deviceGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        deviceGroup.setAttribute('class', 'device-node');
        deviceGroup.setAttribute('transform', `translate(${pos.x}, ${pos.y})`);
        deviceGroup.setAttribute('data-device-id', device.did);
        deviceGroup.addEventListener('click', () => selectDevice(device));

        // 判断设备状态：在线且开启 = on，在线关闭 = off，离线 = offline
        let statusClass = 'offline';
        if (device.online) {
            statusClass = device.power === true ? 'on' : 'off';
        }

        // 设备圆形背景
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('class', `device-circle ${statusClass}`);
        circle.setAttribute('r', 14);
        deviceGroup.appendChild(circle);

        // 设备图标
        const icon = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        icon.setAttribute('class', 'device-emoji');
        icon.setAttribute('dy', '1');
        icon.textContent = getDeviceIcon(device.model);
        deviceGroup.appendChild(icon);

        // 添加悬停事件 - 修复：移除mousemove事件，避免频繁更新导致抖动
        deviceGroup.addEventListener('mouseenter', (e) => showDeviceTooltip(e, device, pos));
        deviceGroup.addEventListener('mouseleave', hideDeviceTooltip);
        // 移除 mousemove 事件，tooltip位置在mouseenter时固定

        // 编辑模式下添加设备拖拽和右键删除功能
        if (state.editMode) {
            deviceGroup.addEventListener('contextmenu', (e) => showDeviceContextMenu(e, device));
            // 添加设备拖拽移动功能
            deviceGroup.addEventListener('mousedown', (e) => startDragDevice(e, device));
            // 编辑模式下改变光标样式
            deviceGroup.style.cursor = 'move';
        } else {
            deviceGroup.style.cursor = 'pointer';
        }

        layer.appendChild(deviceGroup);
    });
}

// 创建设备弹窗元素
function createDeviceTooltip() {
    if (document.getElementById('deviceTooltip')) return;

    const tooltip = document.createElement('div');
    tooltip.id = 'deviceTooltip';
    tooltip.className = 'device-tooltip';
    tooltip.innerHTML = `
        <div class="tooltip-header">
            <div class="tooltip-icon" id="tooltipIcon">💡</div>
            <div>
                <div class="tooltip-title" id="tooltipTitle">设备名称</div>
                <div style="margin-top: 2px;">
                    <span class="tooltip-status" id="tooltipStatus">在线</span>
                </div>
            </div>
        </div>
        <div class="tooltip-content" id="tooltipContent">
            <!-- 动态内容 -->
        </div>
    `;
    document.body.appendChild(tooltip);
}

// 显示设备弹窗 - 增强版：显示所有设备功能状态
function showDeviceTooltip(e, device, pos) {
    const tooltip = document.getElementById('deviceTooltip');
    if (!tooltip) return;

    // 更新图标和名称
    document.getElementById('tooltipIcon').textContent = getDeviceIcon(device.model);
    document.getElementById('tooltipTitle').textContent = device.name;

    // 更新状态标签
    const statusEl = document.getElementById('tooltipStatus');
    if (device.online) {
        const powerState = device.power === true ? '开启' : (device.power === false ? '关闭' : '未知');
        statusEl.textContent = `在线 · ${powerState}`;
        statusEl.className = 'tooltip-status online';
    } else {
        statusEl.textContent = '离线';
        statusEl.className = 'tooltip-status offline';
    }

    // 构建详细信息 - 显示所有功能状态
    const contentEl = document.getElementById('tooltipContent');
    let html = '';

    // 基本属性
    html += createTooltipRow('设备ID', device.did);
    html += createTooltipRow('型号', device.model || 'unknown');
    if (device.room_name) {
        html += createTooltipRow('位置', device.room_name);
    }

    // 设备功能状态分组
    html += '<div class="tooltip-properties">';
    html += '<div class="tooltip-properties-title">设备状态</div>';

    // 电源状态
    if (device.power !== undefined && device.power !== null) {
        const powerText = device.power ? '开启' : '关闭';
        const powerClass = device.power ? 'on' : 'off';
        html += createTooltipRow('电源', powerText, powerClass);
    }

    // 亮度（灯光设备）
    if (device.brightness !== undefined && device.brightness !== null) {
        const brightnessValue = typeof device.brightness === 'number' ? `${device.brightness}%` : device.brightness;
        html += createTooltipRow('亮度', brightnessValue);
    }

    // 色温
    if (device.color_temperature !== undefined && device.color_temperature !== null) {
        html += createTooltipRow('色温', `${device.color_temperature}K`);
    }

    // 颜色
    if (device.color !== undefined && device.color !== null) {
        html += createTooltipRow('颜色', device.color);
    }

    // 温度（空调/传感器）
    if (device.temperature !== undefined && device.temperature !== null) {
        html += createTooltipRow('温度', `${device.temperature}°C`);
    }

    // 目标温度（空调）
    if (device.target_temperature !== undefined && device.target_temperature !== null) {
        html += createTooltipRow('目标温度', `${device.target_temperature}°C`);
    }

    // 湿度
    if (device.humidity !== undefined && device.humidity !== null) {
        html += createTooltipRow('湿度', `${device.humidity}%`);
    }

    // 模式
    if (device.mode !== undefined && device.mode !== null) {
        const modeNames = {
            'cool': '制冷',
            'heat': '制热',
            'fan': '送风',
            'dry': '除湿',
            'auto': '自动'
        };
        const modeText = modeNames[device.mode] || device.mode;
        html += createTooltipRow('模式', modeText);
    }

    // 风速
    if (device.fan_speed !== undefined && device.fan_speed !== null) {
        html += createTooltipRow('风速', device.fan_speed);
    }

    // 窗帘开合度
    if (device.position !== undefined && device.position !== null) {
        html += createTooltipRow('开合度', `${device.position}%`);
    }

    // PM2.5
    if (device.pm25 !== undefined && device.pm25 !== null) {
        html += createTooltipRow('PM2.5', `${device.pm25} μg/m³`);
    }

    // CO2
    if (device.co2 !== undefined && device.co2 !== null) {
        html += createTooltipRow('CO₂', `${device.co2} ppm`);
    }

    // TVOC
    if (device.tvoc !== undefined && device.tvoc !== null) {
        html += createTooltipRow('TVOC', `${device.tvoc} mg/m³`);
    }

    // 甲醛
    if (device.hcho !== undefined && device.hcho !== null) {
        html += createTooltipRow('甲醛', `${device.hcho} mg/m³`);
    }

    // 门锁状态
    if (device.lock_state !== undefined && device.lock_state !== null) {
        const lockText = device.lock_state === 'locked' ? '已上锁' : '未上锁';
        const lockClass = device.lock_state === 'locked' ? 'on' : 'off';
        html += createTooltipRow('锁状态', lockText, lockClass);
    }

    // 门状态
    if (device.door_state !== undefined && device.door_state !== null) {
        const doorText = device.door_state === 'open' ? '开门' : '关门';
        html += createTooltipRow('门状态', doorText);
    }

    // 电池电量
    if (device.battery !== undefined && device.battery !== null) {
        const batteryClass = device.battery < 20 ? 'off' : '';
        html += createTooltipRow('电量', `${device.battery}%`, batteryClass);
    }

    // 信号强度
    if (device.rssi !== undefined && device.rssi !== null) {
        html += createTooltipRow('信号', `${device.rssi} dBm`);
    }

    // 音量（音箱）
    if (device.volume !== undefined && device.volume !== null) {
        html += createTooltipRow('音量', `${device.volume}%`);
    }

    // 播放状态
    if (device.play_state !== undefined && device.play_state !== null) {
        const playText = device.play_state === 'playing' ? '播放中' : '已暂停';
        html += createTooltipRow('播放', playText);
    }

    // 窗帘方向
    if (device.motor_direction !== undefined && device.motor_direction !== null) {
        html += createTooltipRow('电机方向', device.motor_direction);
    }

    // 指示灯
    if (device.led_indicator !== undefined && device.led_indicator !== null) {
        const ledText = device.led_indicator ? '开启' : '关闭';
        html += createTooltipRow('指示灯', ledText);
    }

    // 童锁
    if (device.child_lock !== undefined && device.child_lock !== null) {
        const lockText = device.child_lock ? '锁定' : '未锁定';
        html += createTooltipRow('童锁', lockText);
    }

    // 过滤网寿命
    if (device.filter_life !== undefined && device.filter_life !== null) {
        html += createTooltipRow('滤网寿命', `${device.filter_life}%`);
    }

    // 显示其他未知属性（排除内部字段）
    const knownProps = ['did', 'name', 'model', 'online', 'home_id', 'room_id', 'room_name', 'power',
        'brightness', 'color_temperature', 'color', 'temperature', 'target_temperature', 'humidity',
        'mode', 'fan_speed', 'position', 'pm25', 'co2', 'tvoc', 'hcho', 'lock_state', 'door_state',
        'battery', 'rssi', 'volume', 'play_state', 'motor_direction', 'led_indicator', 'child_lock', 'filter_life'];

    const otherProps = Object.keys(device).filter(key => !knownProps.includes(key));
    if (otherProps.length > 0) {
        html += '<div class="tooltip-properties-title">其他属性</div>';
        otherProps.forEach(key => {
            const value = device[key];
            if (value !== undefined && value !== null && typeof value !== 'object') {
                html += createTooltipRow(key, String(value));
            }
        });
    }

    html += '</div>'; // 结束 tooltip-properties

    contentEl.innerHTML = html;

    // 显示弹窗并设置位置
    tooltip.classList.add('show');
    updateTooltipPositionFromEvent(e);
}

// 固定位置的tooltip显示（用于设备列表）
function showDeviceTooltipFixed(e, device, fixedPos) {
    // 创建一个模拟事件对象
    const simulatedEvent = {
        clientX: fixedPos.x,
        clientY: fixedPos.y
    };
    showDeviceTooltip(simulatedEvent, device, null);
}

// 从鼠标事件更新弹窗位置
function updateTooltipPositionFromEvent(e) {
    const tooltip = document.getElementById('deviceTooltip');
    if (!tooltip || !tooltip.classList.contains('show')) return;

    const padding = 15;
    let x = e.clientX + padding;
    let y = e.clientY + padding;

    // 确保不超出屏幕边界
    const rect = tooltip.getBoundingClientRect();
    if (x + rect.width > window.innerWidth) {
        x = e.clientX - rect.width - padding;
    }
    if (y + rect.height > window.innerHeight) {
        y = e.clientY - rect.height - padding;
    }

    tooltip.style.left = `${x}px`;
    tooltip.style.top = `${y}px`;
}

// 创建弹窗行
function createTooltipRow(label, value, valueClass = '') {
    const valueClassAttr = valueClass ? `tooltip-value ${valueClass}` : 'tooltip-value';
    return `
        <div class="tooltip-row">
            <span class="tooltip-label">${label}</span>
            <span class="${valueClassAttr}">${value}</span>
        </div>
    `;
}

// 更新弹窗位置（用于SVG悬停）
function updateTooltipPosition(e) {
    updateTooltipPositionFromEvent(e);
}

// 隐藏设备弹窗
function hideDeviceTooltip() {
    const tooltip = document.getElementById('deviceTooltip');
    if (tooltip) {
        tooltip.classList.remove('show');
    }
}

// 获取设备图标
function getDeviceIcon(model) {
    const modelLower = (model || '').toLowerCase();
    for (const [key, icon] of Object.entries(DEVICE_ICONS)) {
        if (modelLower.includes(key)) return icon;
    }
    return DEVICE_ICONS.unknown;
}

// 初始化 SVG 交互
function initSVGInteractions() {
    const svg = document.getElementById('floorPlanSvg');

    // 鼠标移动（拖拽和缩放）
    svg.addEventListener('mousemove', (e) => {
        if (state.draggedRoom) {
            handleRoomDrag(e);
        } else if (state.resizedRoom) {
            handleRoomResize(e);
        } else if (state.draggedDevice) {
            handleDeviceDrag(e);
        }
    });

    // 鼠标释放
    svg.addEventListener('mouseup', () => {
        if (state.draggedRoom) {
            endDragRoom();
        } else if (state.resizedRoom) {
            endResizeRoom();
        } else if (state.draggedDevice) {
            endDragDevice();
        }
    });

    // 鼠标离开
    svg.addEventListener('mouseleave', () => {
        if (state.draggedRoom) {
            endDragRoom();
        } else if (state.resizedRoom) {
            endResizeRoom();
        } else if (state.draggedDevice) {
            endDragDevice();
        }
    });
}

// 开始拖拽房间
function startDragRoom(e, room) {
    if (!state.editMode) return;
    e.preventDefault();
    e.stopPropagation();

    state.draggedRoom = room;
    state.selectedRoom = room;

    // 计算偏移
    const svg = document.getElementById('floorPlanSvg');
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

    state.dragOffset = {
        x: svgP.x - room.x,
        y: svgP.y - room.y
    };

    // 高亮选中
    document.querySelectorAll('.room-rect').forEach(r => r.classList.remove('selected'));
    const rect = document.getElementById(`room-rect-${room.id}`);
    if (rect) rect.classList.add('selected');
}

// 开始调整房间大小
function startResizeRoom(e, room) {
    if (!state.editMode) return;
    e.preventDefault();
    e.stopPropagation();

    state.resizedRoom = room;
    state.selectedRoom = room;

    // 高亮选中
    document.querySelectorAll('.room-rect').forEach(r => r.classList.remove('selected'));
    const rect = document.getElementById(`room-rect-${room.id}`);
    if (rect) rect.classList.add('selected');
}

// 处理房间拖拽 - 优化：直接更新DOM而不是重新渲染
function handleRoomDrag(e) {
    if (!state.draggedRoom) return;

    const svg = document.getElementById('floorPlanSvg');
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

    // 更新房间位置
    const newX = Math.max(0, Math.min(900 - state.draggedRoom.width,
        svgP.x - state.dragOffset.x));
    const newY = Math.max(0, Math.min(600 - state.draggedRoom.height,
        svgP.y - state.dragOffset.y));

    state.draggedRoom.x = newX;
    state.draggedRoom.y = newY;

    // 直接更新DOM元素，而不是重新渲染整个户型图
    const rect = document.getElementById(`room-rect-${state.draggedRoom.id}`);
    const text = rect?.nextElementSibling;
    const dragHandle = document.getElementById(`drag-handle-${state.draggedRoom.id}`);
    const resizeHandle = document.getElementById(`resize-handle-${state.draggedRoom.id}`);

    if (rect) {
        rect.setAttribute('x', newX);
        rect.setAttribute('y', newY);
    }
    if (text) {
        text.setAttribute('x', newX + state.draggedRoom.width / 2);
        text.setAttribute('y', newY + state.draggedRoom.height / 2);
    }
    if (dragHandle) {
        dragHandle.setAttribute('cx', newX + state.draggedRoom.width / 2);
        dragHandle.setAttribute('cy', newY + state.draggedRoom.height / 2);
    }
    if (resizeHandle) {
        resizeHandle.setAttribute('x', newX + state.draggedRoom.width - 10);
        resizeHandle.setAttribute('y', newY + state.draggedRoom.height - 10);
    }

    // 更新家具位置
    updateFurniturePosition(state.draggedRoom);
}

// 更新家具位置
function updateFurniturePosition(room) {
    // 家具会随房间移动，这里简化处理，在拖拽结束后再重新渲染
}

// 处理调整大小 - 优化：直接更新DOM + 节流
function handleRoomResize(e) {
    if (!state.resizedRoom) return;

    // 节流处理，限制更新频率
    const now = performance.now();
    if (now - lastResizeTime < THROTTLE_MS) {
        return;
    }
    lastResizeTime = now;

    const svg = document.getElementById('floorPlanSvg');
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

    const minSize = ROOM_TYPES[state.resizedRoom.type]?.minSize || { w: 60, h: 60 };

    // 更新房间大小
    let newWidth = Math.max(minSize.w, svgP.x - state.resizedRoom.x);
    let newHeight = Math.max(minSize.h, svgP.y - state.resizedRoom.y);

    // 限制在画布内
    newWidth = Math.min(newWidth, 900 - state.resizedRoom.x);
    newHeight = Math.min(newHeight, 600 - state.resizedRoom.y);

    state.resizedRoom.width = newWidth;
    state.resizedRoom.height = newHeight;

    // 直接更新DOM元素
    const rect = document.getElementById(`room-rect-${state.resizedRoom.id}`);
    const text = rect?.nextElementSibling;
    const dragHandle = document.getElementById(`drag-handle-${state.resizedRoom.id}`);
    const resizeHandle = document.getElementById(`resize-handle-${state.resizedRoom.id}`);

    if (rect) {
        rect.setAttribute('width', newWidth);
        rect.setAttribute('height', newHeight);
    }
    if (text) {
        text.setAttribute('x', state.resizedRoom.x + newWidth / 2);
        text.setAttribute('y', state.resizedRoom.y + newHeight / 2);
    }
    if (dragHandle) {
        dragHandle.setAttribute('cx', state.resizedRoom.x + newWidth / 2);
        dragHandle.setAttribute('cy', state.resizedRoom.y + newHeight / 2);
    }
    if (resizeHandle) {
        resizeHandle.setAttribute('x', state.resizedRoom.x + newWidth - 10);
        resizeHandle.setAttribute('y', state.resizedRoom.y + newHeight - 10);
    }
}

// 结束调整大小
function endResizeRoom() {
    lastResizeTime = 0;
    if (state.resizedRoom) {
        state.resizedRoom = null;
        // 调整大小结束后重新渲染
        renderFloorPlan();
    }
}

// ========== 设备拖拽移动 ==========

// 开始拖拽设备
function startDragDevice(e, device) {
    if (!state.editMode) return;
    e.preventDefault();
    e.stopPropagation();

    state.draggedDevice = device;
    state.selectedDevice = device;

    // 获取设备当前位置
    let pos = state.floorPlan.device_positions?.[device.did];
    if (!pos) {
        pos = { x: 0, y: 0 };
    }

    // 计算偏移
    const svg = document.getElementById('floorPlanSvg');
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

    state.deviceDragOffset = {
        x: svgP.x - pos.x,
        y: svgP.y - pos.y
    };

    // 添加拖拽中样式
    const deviceNode = document.querySelector(`.device-node[data-device-id="${device.did}"]`);
    if (deviceNode) {
        deviceNode.classList.add('dragging');
    }
}

// 处理设备拖拽
function handleDeviceDrag(e) {
    if (!state.draggedDevice) return;

    const svg = document.getElementById('floorPlanSvg');
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

    // 计算新位置
    let newX = svgP.x - state.deviceDragOffset.x;
    let newY = svgP.y - state.deviceDragOffset.y;

    // 限制在画布范围内
    newX = Math.max(20, Math.min(880, newX));
    newY = Math.max(20, Math.min(580, newY));

    // 更新设备位置
    if (!state.floorPlan.device_positions) {
        state.floorPlan.device_positions = {};
    }

    state.floorPlan.device_positions[state.draggedDevice.did] = {
        device_id: state.draggedDevice.did,
        room_id: null,  // 拖拽时暂时清除房间关联
        x: newX,
        y: newY
    };

    // 直接更新DOM
    const deviceNode = document.querySelector(`.device-node[data-device-id="${state.draggedDevice.did}"]`);
    if (deviceNode) {
        deviceNode.setAttribute('transform', `translate(${newX}, ${newY})`);
    }
}

// 结束设备拖拽
function endDragDevice() {
    if (state.draggedDevice) {
        // 移除拖拽中样式
        const deviceNode = document.querySelector(`.device-node[data-device-id="${state.draggedDevice.did}"]`);
        if (deviceNode) {
            deviceNode.classList.remove('dragging');
        }

        // 检查设备是否在某个房间内，更新房间关联
        const pos = state.floorPlan.device_positions?.[state.draggedDevice.did];
        if (pos) {
            const room = state.floorPlan.rooms.find(r =>
                pos.x >= r.x && pos.x <= r.x + r.width &&
                pos.y >= r.y && pos.y <= r.y + r.height
            );
            if (room) {
                pos.room_id = room.id;
                state.draggedDevice.room_id = room.id;
            }
        }

        state.draggedDevice = null;

        // 显示提示
        showToast('设备位置已更新，点击保存按钮保存更改');
    }
}

// 处理房间拖拽 - 优化：直接更新DOM + 节流
function handleRoomDrag(e) {
    if (!state.draggedRoom) return;

    // 节流处理
    const now = performance.now();
    if (now - lastDragTime < THROTTLE_MS) {
        return;
    }
    lastDragTime = now;

    const svg = document.getElementById('floorPlanSvg');
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

    // 更新房间位置
    const newX = Math.max(0, Math.min(900 - state.draggedRoom.width,
        svgP.x - state.dragOffset.x));
    const newY = Math.max(0, Math.min(600 - state.draggedRoom.height,
        svgP.y - state.dragOffset.y));

    state.draggedRoom.x = newX;
    state.draggedRoom.y = newY;

    // 直接更新DOM元素
    const rect = document.getElementById(`room-rect-${state.draggedRoom.id}`);
    const text = rect?.nextElementSibling;
    const dragHandle = document.getElementById(`drag-handle-${state.draggedRoom.id}`);
    const resizeHandle = document.getElementById(`resize-handle-${state.draggedRoom.id}`);

    if (rect) {
        rect.setAttribute('x', newX);
        rect.setAttribute('y', newY);
    }
    if (text) {
        text.setAttribute('x', newX + state.draggedRoom.width / 2);
        text.setAttribute('y', newY + state.draggedRoom.height / 2);
    }
    if (dragHandle) {
        dragHandle.setAttribute('cx', newX + state.draggedRoom.width / 2);
        dragHandle.setAttribute('cy', newY + state.draggedRoom.height / 2);
    }
    if (resizeHandle) {
        resizeHandle.setAttribute('x', newX + state.draggedRoom.width - 10);
        resizeHandle.setAttribute('y', newY + state.draggedRoom.height - 10);
    }
}

// 结束拖拽
function endDragRoom() {
    lastDragTime = 0;
    if (state.draggedRoom) {
        state.draggedRoom = null;
        // 拖拽结束后重新渲染以更新家具位置
        renderFloorPlan();
    }
}

// 结束拖拽
function endDragRoom() {
    if (state.draggedRoom) {
        state.draggedRoom = null;
        // 拖拽结束后重新渲染以更新家具位置
        renderFloorPlan();
    }
}

// 显示右键菜单
function showContextMenu(e, room) {
    e.preventDefault();
    state.selectedRoom = room;

    const menu = document.getElementById('contextMenu');
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
    menu.classList.add('show');
}

// 隐藏右键菜单
function hideContextMenu() {
    document.getElementById('contextMenu').classList.remove('show');
    document.getElementById('deviceContextMenu').classList.remove('show');
}

// 显示设备右键菜单
function showDeviceContextMenu(e, device) {
    e.preventDefault();
    e.stopPropagation();
    state.selectedDevice = device;

    const menu = document.getElementById('deviceContextMenu');
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
    menu.classList.add('show');
}

// 删除设备
function deleteDevice() {
    hideContextMenu();
    if (!state.selectedDevice || !state.floorPlan) return;

    const deviceName = state.selectedDevice.name || '未命名设备';
    if (!confirm(`确定要删除设备 "${deviceName}" 吗？`)) return;

    // 从户型图中移除设备位置
    if (state.floorPlan.device_positions) {
        delete state.floorPlan.device_positions[state.selectedDevice.did];
    }

    // 清除设备的房间关联
    state.selectedDevice.room_id = null;

    // 清除选中状态
    state.selectedDevice = null;

    // 重新渲染
    renderFloorPlan();
    renderDeviceList();

    // 显示提示
    showToast(`设备 "${deviceName}" 已删除`);
}

function deleteDeviceFromMenu() {
    deleteDevice();
}

// 编辑房间
function editRoom() {
    hideContextMenu();
    if (!state.selectedRoom) return;

    document.getElementById('roomNameInput').value = state.selectedRoom.name;
    document.getElementById('roomWidthInput').value = Math.round(state.selectedRoom.width);
    document.getElementById('roomHeightInput').value = Math.round(state.selectedRoom.height);

    document.getElementById('roomEditModal').classList.add('show');
}

// 关闭房间编辑对话框
function closeRoomEditModal() {
    document.getElementById('roomEditModal').classList.remove('show');
}

// 保存房间编辑
function saveRoomEdit() {
    if (!state.selectedRoom) return;

    const name = document.getElementById('roomNameInput').value;
    const width = parseInt(document.getElementById('roomWidthInput').value);
    const height = parseInt(document.getElementById('roomHeightInput').value);

    if (name) state.selectedRoom.name = name;
    if (width > 50) state.selectedRoom.width = width;
    if (height > 50) state.selectedRoom.height = height;

    closeRoomEditModal();
    renderFloorPlan();
}

// 删除房间
function deleteRoom() {
    hideContextMenu();
    if (!state.selectedRoom || !state.floorPlan) return;

    if (!confirm(`确定要删除房间 "${state.selectedRoom.name}" 吗？`)) return;

    state.floorPlan.rooms = state.floorPlan.rooms.filter(r => r.id !== state.selectedRoom.id);
    state.selectedRoom = null;

    closeRoomEditModal();
    renderFloorPlan();
    updateRoomCount();
}

function deleteRoomFromMenu() {
    deleteRoom();
}

// 切换编辑模式
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
        state.selectedRoom = null;
        state.selectedDevice = null;
        // 隐藏所有右键菜单
        hideContextMenu();
    }

    renderFloorPlan();
}

// 保存户型图
async function saveFloorPlan() {
    if (!state.floorPlan || !state.currentHome) return;

    try {
        const response = await fetch(`/api/homes/${state.currentHome.home_id}/floorplan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state.floorPlan)
        });

        const result = await response.json();
        if (result.success) {
            showToast('户型图已保存');
            // 保存成功后退出编辑模式
            if (state.editMode) {
                toggleEditMode();
            }
        } else {
            showToast('保存失败: ' + result.error, 'error');
        }
    } catch (error) {
        showToast('保存失败: ' + error.message, 'error');
    }
}

// 渲染设备列表
function renderDeviceList() {
    const container = document.getElementById('deviceList');
    const filter = document.getElementById('deviceFilter').value;

    container.innerHTML = '';

    if (state.devices.length === 0) {
        container.innerHTML = '<div class="loading">暂无设备</div>';
        return;
    }

    const filtered = filter === 'all'
        ? state.devices
        : state.devices.filter(d => d.model?.toLowerCase().includes(filter));

    filtered.forEach(device => {
        const el = createDeviceListItem(device);
        container.appendChild(el);
    });
}

// 创建设备列表项
function createDeviceListItem(device) {
    const div = document.createElement('div');
    div.className = 'device-item';
    div.draggable = true;
    div.dataset.deviceId = device.did;

    const isPlaced = state.floorPlan?.device_positions?.[device.did];
    if (isPlaced) div.classList.add('placed');

    // 如果设备开启，添加开启样式
    if (device.power === true) {
        div.classList.add('active');
    }

    const icon = getDeviceIcon(device.model);

    // 状态指示：在线开启 = 绿色发光，在线关闭 = 灰色，离线 = 暗色
    let statusClass = 'offline';
    let statusText = '离线';
    if (device.online) {
        if (device.power === true) {
            statusClass = 'online active';
            statusText = '开启';
        } else {
            statusClass = 'online';
            statusText = '关闭';
        }
    }

    div.innerHTML = `
        <div class="device-status ${statusClass}"></div>
        <div class="device-icon">${icon}</div>
        <div class="device-name">${device.name}</div>
        <div class="device-info">${statusText}</div>
    `;

    // 添加悬停事件显示详情 - 修复：使用固定位置，避免抖动
    div.addEventListener('mouseenter', (e) => {
        // 计算一个固定的位置（在元素右上方）
        const rect = div.getBoundingClientRect();
        const fixedPos = { x: rect.right + 10, y: rect.top };
        showDeviceTooltipFixed(e, device, fixedPos);
    });
    div.addEventListener('mouseleave', hideDeviceTooltip);

    div.addEventListener('dragstart', (e) => handleDeviceDragStart(e, device));

    return div;
}

// 设备拖拽
function handleDeviceDragStart(e, device) {
    e.dataTransfer.setData('deviceId', device.did);
    e.target.classList.add('dragging');
}

// 处理设备放置到房间
async function handleDeviceDropOnRoom(e, room) {
    e.preventDefault();
    e.stopPropagation();

    const deviceId = e.dataTransfer.getData('deviceId');
    if (!deviceId) return;

    const device = state.devices.find(d => d.did === deviceId);
    if (!device) return;

    // 计算放置位置（房间中心）
    const svg = document.getElementById('floorPlanSvg');
    const pt = svg.createSVGPoint();
    pt.x = e.clientX;
    pt.y = e.clientY;
    const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());

    // 确保位置在房间范围内
    const x = Math.max(room.x + 20, Math.min(room.x + room.width - 20, svgP.x));
    const y = Math.max(room.y + 20, Math.min(room.y + room.height - 20, svgP.y));

    // 更新设备位置
    if (!state.floorPlan.device_positions) {
        state.floorPlan.device_positions = {};
    }

    state.floorPlan.device_positions[deviceId] = {
        device_id: deviceId,
        room_id: room.id,
        x: x,
        y: y
    };

    // 更新设备的房间关联
    device.room_id = room.id;

    // 保存到服务器
    await saveDevicePosition(deviceId, room.id, x, y);

    // 重新渲染
    renderFloorPlan();
    renderDeviceList();

    showToast(`设备 "${device.name}" 已放置到 ${room.name}`);
}

// 保存设备位置到服务器
async function saveDevicePosition(deviceId, roomId, x, y) {
    if (!state.currentHome) return;

    try {
        const response = await fetch(`/api/homes/${state.currentHome.home_id}/device-position`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: deviceId,
                room_id: roomId,
                x: x,
                y: y
            })
        });

        const result = await response.json();
        if (!result.success) {
            console.error('保存设备位置失败:', result.error);
        }
    } catch (error) {
        console.error('保存设备位置失败:', error);
        // 前端已更新，即使后端失败也不影响使用
    }
}

// 选择设备
async function selectDevice(device) {
    state.selectedDevice = device;
    await loadDeviceProperties(device);
}

// 加载设备属性
async function loadDeviceProperties(device) {
    const container = document.getElementById('deviceProperties');
    const icon = getDeviceIcon(device.model);
    const statusClass = device.online ? 'online' : 'offline';
    const statusText = device.online ? '在线' : '离线';

    let controlsHtml = '';

    if (device.model?.toLowerCase().includes('light')) {
        controlsHtml = `
            <div class="control-group">
                <label>电源</label>
                <div class="control-row">
                    <div class="switch ${device.power ? 'on' : ''}" onclick="toggleDevice('${device.did}', 'power')"></div>
                    <span>${device.power ? '开启' : '关闭'}</span>
                </div>
            </div>
        `;
    }

    container.innerHTML = `
        <div class="device-detail">
            <div class="device-detail-header">
                <div class="device-detail-icon">${icon}</div>
                <div class="device-detail-info">
                    <h4>${device.name}</h4>
                    <p>${device.model}</p>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
            </div>
            ${controlsHtml}
        </div>
    `;
}

// 控制设备
async function toggleDevice(deviceId, action) {
    // 实现设备控制逻辑
    console.log('控制设备:', deviceId, action);
}

// 场景激活
function activateScene(scene) {
    document.querySelectorAll('.scene-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-scene="${scene}"]`).classList.add('active');

    // 场景逻辑
    const sceneNames = {
        morning: '早上好场景已激活',
        night: '晚安场景已激活',
        movie: '电影场景已激活',
        away: '离家场景已激活'
    };

    showToast(sceneNames[scene] || '场景已激活');
}

// 缩放视图
function zoomView(delta) {
    state.svgScale = Math.max(0.5, Math.min(2, state.svgScale + delta));
    const svg = document.getElementById('floorPlanSvg');
    svg.style.transform = `scale(${state.svgScale})`;
}

// 重置视图
function resetView() {
    state.svgScale = 1;
    const svg = document.getElementById('floorPlanSvg');
    svg.style.transform = 'scale(1)';
}

// 更新房间数量显示
function updateRoomCount() {
    const count = state.floorPlan?.rooms?.length || 0;
    document.getElementById('roomCount').textContent = `${count} 个房间`;
}

// 更新设备数量
function updateDeviceCount() {
    const online = state.devices.filter(d => d.online).length;
    const total = state.devices.length;
    document.getElementById('onlineCount').textContent = `在线: ${online}`;
    document.getElementById('totalCount').textContent = `总计: ${total}`;
}

// 显示提示
function showToast(message, type = 'success') {
    // 简单实现，可以扩展为更好的 UI
    console.log(`[${type}] ${message}`);
}

// 显示错误
function showError(message) {
    console.error('❌', message);
    showToast(message, 'error');
}

// 关闭所有模态框
function closeAllModals() {
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('show'));
}

// 启动应用
document.addEventListener('DOMContentLoaded', init);

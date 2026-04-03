/**
 * 智能家居地图应用 - Three.js 3D版本
 * 支持3D视角交互和房间展示
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
    draggedDevice: null,
    deviceDragOffset: { x: 0, y: 0 },
    dragOffset: { x: 0, y: 0 },
    // Three.js相关
    scene: null,
    camera: null,
    renderer: null,
    controls: null,
    roomMeshes: [],
    deviceMeshes: [],
    raycaster: null,
    mouse: null,
    // 视角
    currentView: 'iso', // 'iso', 'top'
    viewTransitioning: false
};

// 自动刷新定时器
let autoRefreshInterval = null;
const AUTO_REFRESH_MS = 3000;

// 房间类型配置 - 马卡龙色系
const ROOM_TYPES = {
    bedroom: { name: '卧室', color: 0xffd5e8, icon: '🛏️', minSize: { w: 120, h: 100 } },
    living: { name: '客厅', color: 0xd5e8ff, icon: '🛋️', minSize: { w: 180, h: 140 } },
    bathroom: { name: '卫生间', color: 0xd5f5e8, icon: '🚿', minSize: { w: 80, h: 80 } },
    kitchen: { name: '厨房', color: 0xffe8d5, icon: '🍳', minSize: { w: 100, h: 100 } },
    balcony: { name: '阳台', color: 0xe8f5d5, icon: '🌿', minSize: { w: 100, h: 60 } },
    study: { name: '书房', color: 0xe8d5ff, icon: '📚', minSize: { w: 100, h: 90 } },
    entry: { name: '玄关', color: 0xf0f0f5, icon: '🚪', minSize: { w: 80, h: 80 } }
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
    console.log('🚀 初始化智能家居3D地图...');
    initThreeJS();
    bindEvents();
    await loadHomes();
    startAutoRefresh();
    animate();
}

// 初始化Three.js
function initThreeJS() {
    const container = document.getElementById('threeContainer');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // 场景
    state.scene = new THREE.Scene();
    state.scene.background = new THREE.Color(0xf5f7fa);

    // 相机 - 等轴视角
    const aspect = width / height;
    const frustumSize = 800;
    state.camera = new THREE.OrthographicCamera(
        frustumSize * aspect / -2,
        frustumSize * aspect / 2,
        frustumSize / 2,
        frustumSize / -2,
        1,
        2000
    );

    // 渲染器
    state.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    state.renderer.setSize(width, height);
    state.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    state.renderer.shadowMap.enabled = true;
    state.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(state.renderer.domElement);

    // 控制器
    state.controls = new THREE.OrbitControls(state.camera, state.renderer.domElement);
    state.controls.enableDamping = true;
    state.controls.dampingFactor = 0.05;
    state.controls.minZoom = 0.5;
    state.controls.maxZoom = 2;
    state.controls.maxPolarAngle = Math.PI / 2.2; // 限制视角不转到地下

    // 光照
    setupLighting();

    // 射线检测
    state.raycaster = new THREE.Raycaster();
    state.mouse = new THREE.Vector2();

    // 设置初始视角
    setIsoView();

    // 窗口大小调整
    window.addEventListener('resize', onWindowResize);
}

// 设置光照
function setupLighting() {
    // 环境光
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    state.scene.add(ambientLight);

    // 主光源
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.5);
    dirLight.position.set(200, 400, 200);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    dirLight.shadow.camera.near = 0.5;
    dirLight.shadow.camera.far = 1000;
    dirLight.shadow.camera.left = -500;
    dirLight.shadow.camera.right = 500;
    dirLight.shadow.camera.top = 500;
    dirLight.shadow.camera.bottom = -500;
    state.scene.add(dirLight);

    // 补光
    const fillLight = new THREE.DirectionalLight(0xffffff, 0.2);
    fillLight.position.set(-200, 200, -200);
    state.scene.add(fillLight);
}

// 设置等轴视角
function setIsoView() {
    state.currentView = 'iso';
    const distance = 800;
    const angle = Math.PI / 6;

    state.camera.position.set(
        distance * Math.cos(angle),
        distance * 0.8,
        distance * Math.sin(angle)
    );
    state.camera.lookAt(450, 0, 300);
    state.camera.zoom = 1;
    state.camera.updateProjectionMatrix();
    state.controls.update();
}

// 设置顶视角
function setTopView() {
    state.currentView = 'top';
    state.camera.position.set(450, 1000, 300);
    state.camera.lookAt(450, 0, 300);
    state.camera.zoom = 1;
    state.camera.updateProjectionMatrix();
    state.controls.update();
}

// 窗口大小调整
function onWindowResize() {
    const container = document.getElementById('threeContainer');
    const width = container.clientWidth;
    const height = container.clientHeight;

    const aspect = width / height;
    const frustumSize = 800;

    state.camera.left = frustumSize * aspect / -2;
    state.camera.right = frustumSize * aspect / 2;
    state.camera.top = frustumSize / 2;
    state.camera.bottom = frustumSize / -2;
    state.camera.updateProjectionMatrix();

    state.renderer.setSize(width, height);
}

// 动画循环
function animate() {
    requestAnimationFrame(animate);

    // 更新Tween
    TWEEN.update();

    // 更新控制器
    if (state.controls) {
        state.controls.update();
    }

    // 渲染场景
    if (state.renderer && state.scene && state.camera) {
        state.renderer.render(state.scene, state.camera);
    }
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

// 刷新设备状态
async function refreshDeviceStatus() {
    if (!state.currentHome) return;

    try {
        const response = await fetch(`/api/homes/${state.currentHome.home_id}/devices`);
        const data = await response.json();

        if (data.devices) {
            let hasChanges = false;
            data.devices.forEach(newDevice => {
                const oldDevice = state.devices.find(d => d.did === newDevice.did);
                if (oldDevice) {
                    if (oldDevice.power !== newDevice.power ||
                        oldDevice.online !== newDevice.online) {
                        hasChanges = true;
                        Object.assign(oldDevice, newDevice);
                        updateDeviceMesh(oldDevice);
                    }
                } else {
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

// 更新设备3D模型状态
function updateDeviceMesh(device) {
    const mesh = state.deviceMeshes.find(m => m.userData.deviceId === device.did);
    if (mesh) {
        const status = device.online ? (device.power ? 'on' : 'off') : 'offline';
        updateDeviceVisual(mesh, status);
    }
}

// 更新设备视觉效果
function updateDeviceVisual(mesh, status) {
    const circleMesh = mesh.children.find(c => c.userData.isCircle);
    const iconSprite = mesh.children.find(c => c.userData.isIcon);

    if (circleMesh) {
        if (status === 'on') {
            circleMesh.material.color.setHex(0x5cb85c);
            circleMesh.material.emissive.setHex(0x2d5a2d);
            circleMesh.material.emissiveIntensity = 0.3;
        } else if (status === 'off') {
            circleMesh.material.color.setHex(0xffffff);
            circleMesh.material.emissive.setHex(0x000000);
            circleMesh.material.emissiveIntensity = 0;
        } else {
            circleMesh.material.color.setHex(0xcccccc);
            circleMesh.material.emissive.setHex(0x000000);
            circleMesh.material.emissiveIntensity = 0;
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

    // 视角控制
    document.getElementById('resetViewBtn').addEventListener('click', setIsoView);
    document.getElementById('topViewBtn').addEventListener('click', setTopView);
    document.getElementById('isoViewBtn').addEventListener('click', setIsoView);

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

    // 3D场景点击事件
    if (state.renderer) {
        state.renderer.domElement.addEventListener('click', onSceneClick);
        state.renderer.domElement.addEventListener('contextmenu', onSceneRightClick);
        state.renderer.domElement.addEventListener('mousemove', onSceneMouseMove);
    }
}

// 场景点击事件
function onSceneClick(event) {
    if (!state.scene) return;

    const rect = state.renderer.domElement.getBoundingClientRect();
    state.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    state.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    state.raycaster.setFromCamera(state.mouse, state.camera);

    // 检测设备点击
    const deviceIntersects = state.raycaster.intersectObjects(state.deviceMeshes, true);
    if (deviceIntersects.length > 0) {
        const deviceMesh = deviceIntersects[0].object.parent || deviceIntersects[0].object;
        const deviceId = deviceMesh.userData.deviceId;
        const device = state.devices.find(d => d.did === deviceId);
        if (device) {
            selectDevice(device);
        }
        return;
    }

    // 检测房间点击
    const roomIntersects = state.raycaster.intersectObjects(state.roomMeshes);
    if (roomIntersects.length > 0) {
        const roomMesh = roomIntersects[0].object;
        const roomId = roomMesh.userData.roomId;
        const room = state.floorPlan?.rooms.find(r => r.id === roomId);
        if (room) {
            selectRoom(room);
        }
    }
}

// 场景右键事件
function onSceneRightClick(event) {
    if (!state.editMode) return;
    event.preventDefault();

    const rect = state.renderer.domElement.getBoundingClientRect();
    state.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    state.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    state.raycaster.setFromCamera(state.mouse, state.camera);

    const roomIntersects = state.raycaster.intersectObjects(state.roomMeshes);
    if (roomIntersects.length > 0) {
        const roomMesh = roomIntersects[0].object;
        const roomId = roomMesh.userData.roomId;
        const room = state.floorPlan?.rooms.find(r => r.id === roomId);
        if (room) {
            showContextMenu(event, room);
        }
    }
}

// 场景鼠标移动事件
function onSceneMouseMove(event) {
    if (!state.scene) return;

    const rect = state.renderer.domElement.getBoundingClientRect();
    state.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    state.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    state.raycaster.setFromCamera(state.mouse, state.camera);

    // 悬停效果
    const intersects = state.raycaster.intersectObjects(state.roomMeshes);
    state.roomMeshes.forEach(mesh => {
        mesh.material.emissiveIntensity = 0;
    });

    if (intersects.length > 0) {
        const roomMesh = intersects[0].object;
        roomMesh.material.emissive.setHex(0xffffff);
        roomMesh.material.emissiveIntensity = 0.1;
        state.renderer.domElement.style.cursor = 'pointer';
    } else {
        state.renderer.domElement.style.cursor = 'default';
    }
}

// 加载家庭列表
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

    await loadFloorPlan(homeId);
    await loadDevices();
    renderFloorPlan3D();
    updateRoomCount();
}

// 加载户型图
async function loadFloorPlan(homeId) {
    let planLoaded = false;

    try {
        const response = await fetch(`/api/homes/${homeId}/floorplan`);
        const data = await response.json();

        if (!data.error && data.rooms !== undefined && data.rooms !== null) {
            state.floorPlan = data;
            planLoaded = true;
        }
    } catch (error) {
        console.log('户型图API加载失败:', error);
    }

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
        state.floorPlan.rooms = generateRoomLayout(2, 1, 1, 1, 1, 0);
    }
}

// 加载设备
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
            power: Math.random() > 0.5,
            home_id: state.currentHome?.home_id,
            room_id: null
        });
    });
    return devices;
}

// 生成房间布局算法
function generateRoomLayout(bedrooms, living, bathrooms, kitchen, balcony, study) {
    const rooms = [];
    const padding = 20;
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

    // 阳台
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

// 渲染3D户型图
function renderFloorPlan3D() {
    if (!state.scene) return;

    // 清除现有房间和设备
    clearScene();

    if (!state.floorPlan) return;

    // 显示编辑模式指示器
    if (state.editMode) {
        showEditIndicator();
    }

    // 渲染房间
    if (state.floorPlan.rooms) {
        state.floorPlan.rooms.forEach(room => {
            renderRoom3D(room);
        });
    }

    // 渲染设备
    renderDevices3D();
}

// 清除场景
function clearScene() {
    // 移除房间
    state.roomMeshes.forEach(mesh => {
        state.scene.remove(mesh);
        mesh.geometry.dispose();
        mesh.material.dispose();
    });
    state.roomMeshes = [];

    // 移除设备
    state.deviceMeshes.forEach(mesh => {
        state.scene.remove(mesh);
        mesh.children.forEach(child => {
            if (child.geometry) child.geometry.dispose();
            if (child.material) {
                if (Array.isArray(child.material)) {
                    child.material.forEach(m => m.dispose());
                } else {
                    child.material.dispose();
                }
            }
        });
    });
    state.deviceMeshes = [];

    // 移除指示器
    const indicator = document.querySelector('.edit-indicator');
    if (indicator) indicator.remove();
}

// 渲染3D房间
function renderRoom3D(room) {
    const roomConfig = ROOM_TYPES[room.type];
    const color = roomConfig?.color || 0xf0f0f5;

    // 创建房间组
    const roomGroup = new THREE.Group();
    roomGroup.userData = { roomId: room.id, isRoom: true };

    // 地板
    const floorGeometry = new THREE.BoxGeometry(room.width, 2, room.height);
    const floorMaterial = new THREE.MeshLambertMaterial({
        color: color,
        transparent: true,
        opacity: 0.9
    });
    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.position.set(
        room.x + room.width / 2,
        -1,
        room.y + room.height / 2
    );
    floor.userData = { roomId: room.id, isRoom: true };
    floor.castShadow = true;
    floor.receiveShadow = true;
    roomGroup.add(floor);
    state.roomMeshes.push(floor);

    // 墙壁 - 四面
    const wallHeight = 40;
    const wallThickness = 2;

    // 后墙
    const backWall = createWall(room.width + wallThickness * 2, wallHeight, wallThickness, color);
    backWall.position.set(room.x + room.width / 2, wallHeight / 2, room.y - wallThickness / 2);
    roomGroup.add(backWall);

    // 前墙
    const frontWall = createWall(room.width + wallThickness * 2, wallHeight, wallThickness, color);
    frontWall.position.set(room.x + room.width / 2, wallHeight / 2, room.y + room.height + wallThickness / 2);
    roomGroup.add(frontWall);

    // 左墙
    const leftWall = createWall(wallThickness, wallHeight, room.height, color);
    leftWall.position.set(room.x - wallThickness / 2, wallHeight / 2, room.y + room.height / 2);
    roomGroup.add(leftWall);

    // 右墙
    const rightWall = createWall(wallThickness, wallHeight, room.height, color);
    rightWall.position.set(room.x + room.width + wallThickness / 2, wallHeight / 2, room.y + room.height / 2);
    roomGroup.add(rightWall);

    // 房间标签
    const label = createTextSprite(room.name, 48);
    label.position.set(room.x + room.width / 2, wallHeight + 10, room.y + room.height / 2);
    roomGroup.add(label);

    state.scene.add(roomGroup);
}

// 创建墙壁
function createWall(width, height, depth, color) {
    const geometry = new THREE.BoxGeometry(width, height, depth);
    const material = new THREE.MeshLambertMaterial({
        color: color,
        transparent: true,
        opacity: 0.6
    });
    const wall = new THREE.Mesh(geometry, material);
    wall.castShadow = true;
    wall.receiveShadow = true;
    return wall;
}

// 创建设备3D标记
function renderDevices3D() {
    state.devices.forEach(device => {
        let pos = state.floorPlan?.device_positions?.[device.did];
        if (!pos) {
            const room = state.floorPlan?.rooms.find(r => r.id === device.room_id);
            if (room) {
                pos = {
                    x: room.x + room.width / 2,
                    y: room.y + room.height / 2
                };
            }
        }

        if (!pos) return;

        const deviceGroup = createDeviceMarker(device, pos);
        state.deviceMeshes.push(deviceGroup);
        state.scene.add(deviceGroup);
    });
}

// 创建设备标记
function createDeviceMarker(device, pos) {
    const group = new THREE.Group();
    group.userData = { deviceId: device.did, isDevice: true };

    // 状态判断
    const status = device.online ? (device.power ? 'on' : 'off') : 'offline';

    // 悬浮动画基础位置
    group.userData.baseY = 60;
    group.userData.floatOffset = Math.random() * Math.PI * 2;

    // 圆形背景
    const circleGeometry = new THREE.CylinderGeometry(15, 15, 4, 32);
    let circleColor = 0xffffff;
    let emissiveColor = 0x000000;
    let emissiveIntensity = 0;

    if (status === 'on') {
        circleColor = 0x5cb85c;
        emissiveColor = 0x2d5a2d;
        emissiveIntensity = 0.3;
    } else if (status === 'offline') {
        circleColor = 0xcccccc;
    }

    const circleMaterial = new THREE.MeshLambertMaterial({
        color: circleColor,
        emissive: emissiveColor,
        emissiveIntensity: emissiveIntensity
    });
    const circle = new THREE.Mesh(circleGeometry, circleMaterial);
    circle.userData = { isCircle: true };
    circle.rotation.x = 0;
    circle.position.y = 0;
    group.add(circle);

    // 连接线
    const lineGeometry = new THREE.CylinderGeometry(1, 1, 40, 8);
    const lineMaterial = new THREE.MeshBasicMaterial({
        color: 0xcccccc,
        transparent: true,
        opacity: 0.5
    });
    const line = new THREE.Mesh(lineGeometry, lineMaterial);
    line.position.y = -22;
    group.add(line);

    // 设备图标
    const icon = getDeviceIcon(device.model);
    const iconSprite = createEmojiSprite(icon, 24);
    iconSprite.userData = { isIcon: true };
    iconSprite.position.y = 0;
    group.add(iconSprite);

    // 位置设置
    group.position.set(pos.x, group.userData.baseY, pos.y);

    return group;
}

// 创建文字精灵
function createTextSprite(text, fontSize = 48) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 512;
    canvas.height = 128;

    context.font = `bold ${fontSize}px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif`;
    context.fillStyle = 'rgba(0, 0, 0, 0.7)';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText(text, 256, 64);

    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(canvas.width / 4, canvas.height / 4, 1);

    return sprite;
}

// 创建表情符号精灵
function createEmojiSprite(emoji, size = 32) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 64;
    canvas.height = 64;

    context.font = `${size}px serif`;
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText(emoji, 32, 36);

    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(20, 20, 1);

    return sprite;
}

// 获取设备图标
function getDeviceIcon(model) {
    const modelLower = (model || '').toLowerCase();
    for (const [key, icon] of Object.entries(DEVICE_ICONS)) {
        if (modelLower.includes(key)) return icon;
    }
    return DEVICE_ICONS.unknown;
}

// 显示编辑模式指示器
function showEditIndicator() {
    const wrapper = document.querySelector('.floor-plan-wrapper');
    const indicator = document.createElement('div');
    indicator.className = 'edit-indicator';
    indicator.textContent = '📐 编辑模式：点击房间或设备进行编辑';
    wrapper.appendChild(indicator);
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
    renderFloorPlan3D();
    updateRoomCount();

    if (!state.editMode) {
        toggleEditMode();
    }
}

// 选择设备
async function selectDevice(device) {
    state.selectedDevice = device;
    await loadDeviceProperties(device);
}

// 选择房间
function selectRoom(room) {
    state.selectedRoom = room;
    if (state.editMode) {
        highlightRoom(room.id);
    }
}

// 高亮房间
function highlightRoom(roomId) {
    state.roomMeshes.forEach(mesh => {
        if (mesh.userData.roomId === roomId) {
            mesh.material.emissive.setHex(0x4a90d9);
            mesh.material.emissiveIntensity = 0.3;
        } else {
            mesh.material.emissive.setHex(0x000000);
            mesh.material.emissiveIntensity = 0;
        }
    });
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
    console.log('控制设备:', deviceId, action);
}

// 加载设备列表
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

    if (device.power === true) {
        div.classList.add('active');
    }

    const icon = getDeviceIcon(device.model);

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

    div.addEventListener('click', () => selectDevice(device));
    div.addEventListener('dragstart', (e) => handleDeviceDragStart(e, device));

    return div;
}

// 设备拖拽
function handleDeviceDragStart(e, device) {
    e.dataTransfer.setData('deviceId', device.did);
    e.target.classList.add('dragging');
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
        showEditIndicator();
    } else {
        btn.textContent = '✏️ 编辑';
        btn.classList.remove('btn-success');
        saveBtn.style.display = 'none';
        state.selectedRoom = null;
        state.selectedDevice = null;
        hideContextMenu();

        const indicator = document.querySelector('.edit-indicator');
        if (indicator) indicator.remove();
    }

    // 重新渲染以更新交互
    renderFloorPlan3D();
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
    renderFloorPlan3D();
}

// 删除房间
function deleteRoom() {
    hideContextMenu();
    if (!state.selectedRoom || !state.floorPlan) return;

    if (!confirm(`确定要删除房间 "${state.selectedRoom.name}" 吗？`)) return;

    state.floorPlan.rooms = state.floorPlan.rooms.filter(r => r.id !== state.selectedRoom.id);
    state.selectedRoom = null;

    closeRoomEditModal();
    renderFloorPlan3D();
    updateRoomCount();
}

function deleteRoomFromMenu() {
    deleteRoom();
}

// 删除设备
function deleteDevice() {
    hideContextMenu();
    if (!state.selectedDevice || !state.floorPlan) return;

    const deviceName = state.selectedDevice.name || '未命名设备';
    if (!confirm(`确定要删除设备 "${deviceName}" 吗？`)) return;

    if (state.floorPlan.device_positions) {
        delete state.floorPlan.device_positions[state.selectedDevice.did];
    }

    state.selectedDevice.room_id = null;
    state.selectedDevice = null;

    renderFloorPlan3D();
    renderDeviceList();
    showToast(`设备 "${deviceName}" 已删除`);
}

function deleteDeviceFromMenu() {
    deleteDevice();
}

// 场景激活
function activateScene(scene) {
    document.querySelectorAll('.scene-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-scene="${scene}"]`).classList.add('active');

    const sceneNames = {
        morning: '早上好场景已激活',
        night: '晚安场景已激活',
        movie: '电影场景已激活',
        away: '离家场景已激活'
    };

    showToast(sceneNames[scene] || '场景已激活');
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
    console.log(`[${type}] ${message}`);
}

// 关闭所有模态框
function closeAllModals() {
    document.querySelectorAll('.modal').forEach(m => m.classList.remove('show'));
}

// 启动应用
document.addEventListener('DOMContentLoaded', init);

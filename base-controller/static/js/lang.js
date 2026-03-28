/* Roban Swarm — Internationalization (i18n) */

const I18N = (() => {
    const translations = {
        en: {
            // Header
            title: "Roban Swarm",
            sim_banner: "SIMULATION MODE — Targeting sim helis (sysid +100)",

            // Nav
            nav_dashboard: "Dashboard",
            nav_fleet: "Fleet",
            nav_show: "Show",
            nav_config: "Config",

            // Dashboard
            fleet_overview: "Fleet Overview",
            refresh: "Refresh",
            base_station: "Base Station",
            no_vehicles: "No vehicles registered. Go to Fleet to add helis.",

            // Heli card labels
            lbl_ip: "IP",
            lbl_gps: "GPS",
            lbl_sats: "Sats",
            lbl_hdop: "HDOP",
            lbl_batt: "Batt",
            lbl_mode: "Mode",
            lbl_armed: "Armed",
            lbl_sysid: "SysID",
            lbl_fw: "FW",
            lbl_yes: "Yes",
            lbl_no: "No",
            lbl_rtcm: "RTCM",
            lbl_clients: "Clients",
            lbl_total: "Total",

            // GPS fix labels
            gps_nofix: "No Fix",
            gps_2d: "2D",
            gps_3d: "3D",
            gps_dgps: "DGPS",
            gps_float: "Float",
            gps_rtk: "RTK",

            // Fleet page
            fleet_manager: "Fleet Manager",
            btn_add: "Add",
            btn_remove: "Remove",
            btn_apply: "Apply Changes",

            // Show page
            show_control: "Show Control",
            btn_upload: "Upload Show",
            btn_lineup: "Capture Lineup",
            btn_preflight: "Preflight",
            btn_fix: "Fix Issues",
            btn_launch: "Launch",
            btn_go: "GO",
            btn_pause: "Pause",
            btn_resume: "Resume",
            btn_land: "Land",
            btn_rtl: "RTL ALL",
            btn_stop: "STOP",
            preflight_checks: "Pre-flight Checks",
            event_log: "Event Log",
            telemetry: "Telemetry",
            map_2d: "2D Map",
            lineup: "Lineup",

            // Show states
            state_idle: "IDLE",
            state_loaded: "LOADED",
            state_lineup_ready: "LINEUP READY",
            state_preflight_ok: "PREFLIGHT OK",
            state_arming: "ARMING",
            state_spooling: "SPOOLING",
            state_taking_off: "TAKING OFF",
            state_staging: "STAGING",
            state_running: "RUNNING",
            state_paused: "PAUSED",
            state_landing: "LANDING",
            state_done: "DONE",
            state_rtl: "RTL",
            state_error: "ERROR",

            // Confirmations
            confirm_launch: "Launch all helis? This will ARM and TAKE OFF.",
            confirm_land: "Start landing sequence?",
            confirm_rtl: "EMERGENCY RTL — All helis return to home with staggered altitudes. ArduPilot takes over. Proceed?",
            confirm_stop: "EMERGENCY STOP — BRAKE all helis immediately?",

            // Config page
            config_console: "Config Console",
            select_heli: "Select Heli:",
            btn_connect_gcs: "Connect to GCS",
            btn_production: "Production Mode",
            fleet_param_map: "Fleet Parameter Map",
            btn_check_params: "Check All Params",
            param_details: "Parameter Details",

            // Footer
            connecting: "Connecting...",
            connected: "Connected",
            disconnected: "Disconnected — reconnecting...",
        },

        de: {
            title: "Roban Schwarm",
            sim_banner: "SIMULATIONSMODUS — Sim-Helis aktiv (SysID +100)",
            nav_dashboard: "Dashboard",
            nav_fleet: "Flotte",
            nav_show: "Show",
            nav_config: "Konfig",
            fleet_overview: "Flottenübersicht",
            refresh: "Aktualisieren",
            base_station: "Basisstation",
            no_vehicles: "Keine Fahrzeuge registriert. Helis unter Flotte hinzufügen.",
            lbl_ip: "IP",
            lbl_gps: "GPS",
            lbl_sats: "Sats",
            lbl_hdop: "HDOP",
            lbl_batt: "Akku",
            lbl_mode: "Modus",
            lbl_armed: "Scharf",
            lbl_sysid: "SysID",
            lbl_fw: "FW",
            lbl_yes: "Ja",
            lbl_no: "Nein",
            lbl_rtcm: "RTCM",
            lbl_clients: "Clients",
            lbl_total: "Gesamt",
            gps_nofix: "Kein Fix",
            gps_2d: "2D",
            gps_3d: "3D",
            gps_dgps: "DGPS",
            gps_float: "Float",
            gps_rtk: "RTK",
            fleet_manager: "Flottenmanager",
            btn_add: "Hinzufügen",
            btn_remove: "Entfernen",
            btn_apply: "Änderungen anwenden",
            show_control: "Show-Steuerung",
            btn_upload: "Show hochladen",
            btn_lineup: "Aufstellung erfassen",
            btn_preflight: "Vorflugprüfung",
            btn_fix: "Probleme beheben",
            btn_launch: "Start",
            btn_go: "LOS",
            btn_pause: "Pause",
            btn_resume: "Fortsetzen",
            btn_land: "Landen",
            btn_rtl: "RTL ALLE",
            btn_stop: "STOPP",
            preflight_checks: "Vorflugprüfungen",
            event_log: "Ereignisprotokoll",
            telemetry: "Telemetrie",
            map_2d: "2D-Karte",
            lineup: "Aufstellung",
            state_idle: "BEREIT",
            state_loaded: "GELADEN",
            state_lineup_ready: "AUFSTELLUNG OK",
            state_preflight_ok: "VORFLUG OK",
            state_arming: "SCHARFSCHALTEN",
            state_spooling: "HOCHFAHREN",
            state_taking_off: "ABHEBEN",
            state_staging: "POSITIONIEREN",
            state_running: "LÄUFT",
            state_paused: "PAUSIERT",
            state_landing: "LANDUNG",
            state_done: "FERTIG",
            state_rtl: "RTL",
            state_error: "FEHLER",
            confirm_launch: "Alle Helis starten? Dies wird SCHARFSCHALTEN und ABHEBEN.",
            confirm_land: "Landesequenz starten?",
            confirm_rtl: "NOTFALL RTL — Alle Helis kehren mit gestaffelten Höhen zurück. ArduPilot übernimmt. Fortfahren?",
            confirm_stop: "NOTSTOPP — Alle Helis sofort bremsen?",
            config_console: "Konfigurationskonsole",
            select_heli: "Heli wählen:",
            btn_connect_gcs: "Mit GCS verbinden",
            btn_production: "Produktionsmodus",
            fleet_param_map: "Flotten-Parameter",
            btn_check_params: "Alle Parameter prüfen",
            param_details: "Parameterdetails",
            connecting: "Verbinde...",
            connected: "Verbunden",
            disconnected: "Getrennt — verbinde erneut...",
        },

        es: {
            title: "Roban Enjambre",
            sim_banner: "MODO SIMULACIÓN — Helis simulados activos (SysID +100)",
            nav_dashboard: "Panel",
            nav_fleet: "Flota",
            nav_show: "Show",
            nav_config: "Config",
            fleet_overview: "Vista de Flota",
            refresh: "Actualizar",
            base_station: "Estación Base",
            no_vehicles: "Sin vehículos registrados. Añade helis en Flota.",
            lbl_ip: "IP",
            lbl_gps: "GPS",
            lbl_sats: "Sats",
            lbl_hdop: "HDOP",
            lbl_batt: "Batería",
            lbl_mode: "Modo",
            lbl_armed: "Armado",
            lbl_sysid: "SysID",
            lbl_fw: "FW",
            lbl_yes: "Sí",
            lbl_no: "No",
            lbl_rtcm: "RTCM",
            lbl_clients: "Clientes",
            lbl_total: "Total",
            gps_nofix: "Sin Fix",
            gps_2d: "2D",
            gps_3d: "3D",
            gps_dgps: "DGPS",
            gps_float: "Float",
            gps_rtk: "RTK",
            fleet_manager: "Gestor de Flota",
            btn_add: "Añadir",
            btn_remove: "Eliminar",
            btn_apply: "Aplicar Cambios",
            show_control: "Control de Show",
            btn_upload: "Subir Show",
            btn_lineup: "Capturar Alineación",
            btn_preflight: "Prevuelo",
            btn_fix: "Corregir",
            btn_launch: "Lanzar",
            btn_go: "¡YA!",
            btn_pause: "Pausa",
            btn_resume: "Reanudar",
            btn_land: "Aterrizar",
            btn_rtl: "RTL TODO",
            btn_stop: "PARAR",
            preflight_checks: "Verificaciones Prevuelo",
            event_log: "Registro de Eventos",
            telemetry: "Telemetría",
            map_2d: "Mapa 2D",
            lineup: "Alineación",
            state_idle: "INACTIVO",
            state_loaded: "CARGADO",
            state_lineup_ready: "ALINEACIÓN OK",
            state_preflight_ok: "PREVUELO OK",
            state_arming: "ARMANDO",
            state_spooling: "ACELERANDO",
            state_taking_off: "DESPEGANDO",
            state_staging: "POSICIONANDO",
            state_running: "EN MARCHA",
            state_paused: "PAUSADO",
            state_landing: "ATERRIZANDO",
            state_done: "TERMINADO",
            state_rtl: "RTL",
            state_error: "ERROR",
            confirm_launch: "¿Lanzar todos los helis? Esto ARMARÁ y DESPEGARÁ.",
            confirm_land: "¿Iniciar secuencia de aterrizaje?",
            confirm_rtl: "RTL DE EMERGENCIA — Todos los helis regresan con altitudes escalonadas. ArduPilot toma el control. ¿Continuar?",
            confirm_stop: "PARADA DE EMERGENCIA — ¿Frenar todos los helis inmediatamente?",
            config_console: "Consola de Configuración",
            select_heli: "Seleccionar Heli:",
            btn_connect_gcs: "Conectar a GCS",
            btn_production: "Modo Producción",
            fleet_param_map: "Parámetros de Flota",
            btn_check_params: "Verificar Parámetros",
            param_details: "Detalles de Parámetros",
            connecting: "Conectando...",
            connected: "Conectado",
            disconnected: "Desconectado — reconectando...",
        },

        zh: {
            title: "Roban 蜂群",
            sim_banner: "仿真模式 — 目标仿真直升机 (SysID +100)",
            nav_dashboard: "仪表板",
            nav_fleet: "机队",
            nav_show: "表演",
            nav_config: "配置",
            fleet_overview: "机队概览",
            refresh: "刷新",
            base_station: "基站",
            no_vehicles: "未注册飞行器。请在机队页面添加直升机。",
            lbl_ip: "IP",
            lbl_gps: "GPS",
            lbl_sats: "卫星",
            lbl_hdop: "HDOP",
            lbl_batt: "电池",
            lbl_mode: "模式",
            lbl_armed: "解锁",
            lbl_sysid: "系统ID",
            lbl_fw: "固件",
            lbl_yes: "是",
            lbl_no: "否",
            lbl_rtcm: "RTCM",
            lbl_clients: "客户端",
            lbl_total: "总计",
            gps_nofix: "无定位",
            gps_2d: "2D",
            gps_3d: "3D",
            gps_dgps: "DGPS",
            gps_float: "浮点",
            gps_rtk: "RTK",
            fleet_manager: "机队管理",
            btn_add: "添加",
            btn_remove: "删除",
            btn_apply: "应用更改",
            show_control: "表演控制",
            btn_upload: "上传表演",
            btn_lineup: "采集阵列",
            btn_preflight: "飞行前检查",
            btn_fix: "修复问题",
            btn_launch: "发射",
            btn_go: "开始！",
            btn_pause: "暂停",
            btn_resume: "继续",
            btn_land: "降落",
            btn_rtl: "全部返航",
            btn_stop: "紧急停止",
            preflight_checks: "飞行前检查",
            event_log: "事件日志",
            telemetry: "遥测数据",
            map_2d: "2D地图",
            lineup: "阵列",
            state_idle: "空闲",
            state_loaded: "已加载",
            state_lineup_ready: "阵列就绪",
            state_preflight_ok: "检查通过",
            state_arming: "解锁中",
            state_spooling: "预热中",
            state_taking_off: "起飞中",
            state_staging: "就位中",
            state_running: "执行中",
            state_paused: "已暂停",
            state_landing: "降落中",
            state_done: "完成",
            state_rtl: "返航",
            state_error: "错误",
            confirm_launch: "发射所有直升机？这将解锁并起飞。",
            confirm_land: "开始降落序列？",
            confirm_rtl: "紧急返航 — 所有直升机以阶梯高度返回。ArduPilot接管控制。继续？",
            confirm_stop: "紧急停止 — 立即制动所有直升机？",
            config_console: "配置控制台",
            select_heli: "选择直升机：",
            btn_connect_gcs: "连接地面站",
            btn_production: "生产模式",
            fleet_param_map: "机队参数表",
            btn_check_params: "检查所有参数",
            param_details: "参数详情",
            connecting: "连接中...",
            connected: "已连接",
            disconnected: "已断开 — 重新连接中...",
        },
    };

    let currentLang = localStorage.getItem('roban_lang') || 'en';

    function t(key) {
        return (translations[currentLang] && translations[currentLang][key])
            || translations.en[key]
            || key;
    }

    function setLang(lang) {
        if (!translations[lang]) return;
        currentLang = lang;
        localStorage.setItem('roban_lang', lang);
        applyAll();
    }

    function getLang() { return currentLang; }

    function applyAll() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = t(key);
            } else if (el.tagName === 'OPTION') {
                el.textContent = t(key);
            } else {
                el.textContent = t(key);
            }
        });
        // Update document title
        document.title = t('title') + ' Controller';
        // Update lang selector
        const sel = document.getElementById('lang-select');
        if (sel) sel.value = currentLang;
    }

    // Apply on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyAll);
    } else {
        applyAll();
    }

    return { t, setLang, getLang, applyAll, translations };
})();

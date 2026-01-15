traffic_module_template = {
    'panel': '{name}=script-name={name},update-interval={update_interval}',
    'script': '{name}=type=generic,timeout=10,script-path=https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Module/Panel/Sub-info/Moore/Sub-info.js,script-update-interval=0,argument=url={url}&reset_day={reset}&title={name}&icon=waveform&color={color}'
}

# 固定策略组列表
FIXED_POLICIES = [
    "DIRECT",
    "REJECT",
    "🚀 节点选择",
    "🔧 手动切换",
    "🌍 国外媒体",
    "📲 电报信息",
    "🍎 苹果服务",
    "💬 Ai平台",
    "📢 谷歌FCM",
    "📹 油管视频",
    "📺 哔哩哔哩",
    "Ⓜ️ 微软云盘",
    "🎮 游戏平台",
    "🌏 国内媒体",
    "🎥 奈飞视频",
    "Ⓜ️ 微软服务",
    "📺 巴哈姆特",
    "Ⓜ️ 微软Bing",
    "🎯 全球直连",
    "🛑 全球拦截",
    "🍃 应用净化",
    "🐟 漏网之鱼"
]

# 动态区域策略列表
REGION_POLICIES = [
    "🇭🇰 香港",
    "🇯🇵 日本",
    "🇺🇸 美国",
    "🇸🇬 狮城",
    "🇬🇧 英国",
    "🇨🇳 台湾"
]

conf_template = (
    "#!MANAGED-CONFIG {cos_url}"
    + " interval={update_interval} strict=false"
    + """
[General]
loglevel = notify
bypass-system = true
skip-proxy = 127.0.0.1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,100.64.0.0/10,localhost,*.local,e.crashlytics.com,captive.apple.com,::ffff:0:0:0:0/1,::ffff:128:0:0:0/1
http-listen = 127.0.0.1:7891
socks5-listen = 127.0.0.1:7890
test-timeout = 5
bypass-tun = 192.168.0.0/16,10.0.0.0/8,172.16.0.0/12
dns-server = system, 119.29.29.29, 223.5.5.5, 8.8.8.8

[Panel]
{module_panel}
stream-all = script-name=stream-all, title="流媒体解锁检测", content="请刷新面板", update-interval={update_interval}

[Script]
{module_script}
stream-all = type=generic, timeout=15, script-path=https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Module/Panel/Stream-All/Moore/Stream-All.js

[Proxy]
DIRECT = direct
{proxies}

[Proxy Group]
🚀 节点选择 = select,DIRECT,🔧 手动切换,{regions}
🔧 手动切换 = select,DIRECT,{proxies_one_line}
🌍 国外媒体 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
📲 电报信息 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
🍎 苹果服务 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
💬 Ai平台 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
📢 谷歌FCM = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
📹 油管视频 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
📺 哔哩哔哩 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
Ⓜ️ 微软云盘 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
🎮 游戏平台 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
🌏 国内媒体 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
🎥 奈飞视频 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
Ⓜ️ 微软服务 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
📺 巴哈姆特 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
Ⓜ️ 微软Bing = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
🎯 全球直连 = select,DIRECT,🚀 节点选择
🛑 全球拦截 = select,REJECT,🎯 全球直连
🍃 应用净化 = select,REJECT,🎯 全球直连
🐟 漏网之鱼 = select,🚀 节点选择,🎯 全球直连,🔧 手动切换,{regions}
———————配置——————— = select,DIRECT
{region_strategy}
———————自动——————— = select,DIRECT
{region_auto}

[Rule]
{rule_sets}
GEOIP,CN,🎯 全球直连
FINAL,🐟 漏网之鱼

[Host]
{host}
"""
)

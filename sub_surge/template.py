traffic_module_template = {
    'panel': '{name}=script-name={name},update-interval={update_interval}',
    'script': '{name}=type=generic,timeout=10,script-path=https://raw.githubusercontent.com/Rabbit-Spec/Surge/Master/Module/Panel/Sub-info/Moore/Sub-info.js,script-update-interval=0,argument=url={url}&reset_day={reset}&title={name}&icon=waveform&color={color}'
}

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
DOMAIN-SUFFIX,jp,🇯🇵 日本
RULE-SET,https://raw.githubusercontent.com/Rhythmicc/ACL4SSR/master/Clash/us.list,🇺🇸 美国,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/Rhythmicc/ACL4SSR/master/Clash/direct.list,DIRECT,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/LocalAreaNetwork.list,🎯 全球直连,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/UnBan.list,🎯 全球直连,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanAD.list,🛑 全球拦截,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanProgramAD.list,🍃 应用净化,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/GoogleFCM.list,📢 谷歌FCM,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/GoogleCN.list,🎯 全球直连,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/SteamCN.list,🎯 全球直连,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Microsoft.list,Ⓜ️ 微软服务,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Apple.list,🍎 苹果服务,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Telegram.list,📲 电报信息,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ProxyMedia.list,🌍 国外媒体,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ProxyLite.list,🚀 节点选择,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaDomain.list,🎯 全球直连,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaCompanyIp.list,🎯 全球直连,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Bing.list,Ⓜ️ 微软Bing,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/OneDrive.list,Ⓜ️ 微软云盘,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/AI.list,💬 Ai平台,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/OpenAi.list,💬 Ai平台,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/NetEaseMusic.list,🎯 全球直连,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Epic.list,🎮 游戏平台,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Origin.list,🎮 游戏平台,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Sony.list,🎮 游戏平台,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Steam.list,🎮 游戏平台,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Nintendo.list,🎮 游戏平台,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/YouTube.list,📹 油管视频,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Netflix.list,🎥 奈飞视频,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Bahamut.list,📺 巴哈姆特,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/BilibiliHMT.list,📺 哔哩哔哩,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Bilibili.list,📺 哔哩哔哩,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaMedia.list,🌏 国内媒体,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ProxyGFWlist.list,🚀 节点选择,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Download.list,🎯 全球直连,update-interval=86400
GEOIP,CN,🎯 全球直连
FINAL,🐟 漏网之鱼

[Host]
{host}
"""
)

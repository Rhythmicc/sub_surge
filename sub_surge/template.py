from . import config

conf_template = (
    "#!MANAGED-CONFIG {cos_url}"
    + f" interval={config.select('interval')} strict=false"
    + """
[General]
loglevel = notify
bypass-system = true
skip-proxy = 127.0.0.1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,100.64.0.0/10,localhost,*.local,e.crashlytics.com,captive.apple.com,::ffff:0:0:0:0/1,::ffff:128:0:0:0/1
http-listen = 127.0.0.1:7891
socks5-listen = 127.0.0.1:7890
test-timeout = 5
bypass-tun = 192.168.0.0/16,10.0.0.0/8,172.16.0.0/12
dns-server = 119.29.29.29,223.5.5.5
allow-wifi-access = true
wifi-access-http-port = 7891
wifi-access-socks5-port = 7890


[Proxy]
DIRECT = direct
{proxies}

[Proxy Group]
📒 机场信息 = select,{infos}
🚀 节点选择 = select,DIRECT,🔧 手动切换,🇭🇰 香港,🇯🇵 日本,🇺🇸 美国,🇸🇬 狮城,🇬🇧 英国,🇨🇳 台湾
🔧 手动切换 = select,DIRECT,{proxies_one_line}
🌍 国外媒体 = select,🚀 节点选择,🎯 全球直连,🇭🇰 香港,🇯🇵 日本,🇺🇸 美国,🇸🇬 狮城,🇬🇧 英国,🇨🇳 台湾
📲 电报信息 = select,🚀 节点选择,🎯 全球直连,{proxies_one_line}
Ⓜ️ 微软服务 = select,🚀 节点选择,🎯 全球直连,{proxies_one_line}
🍎 苹果服务 = select,🚀 节点选择,🎯 全球直连,{proxies_one_line}
📢 谷歌FCM = select,🚀 节点选择,🎯 全球直连,{proxies_one_line}
🎯 全球直连 = select,DIRECT,🚀 节点选择
🛑 全球拦截 = select,REJECT,🎯 全球直连
🍃 应用净化 = select,REJECT,🎯 全球直连
🐟 漏网之鱼 = select,🚀 节点选择,🎯 全球直连,{proxies_one_line}
———————配置——————— = select,DIRECT
🇭🇰 香港 = select,🇭🇰 香港最佳,🇭🇰 香港均衡,🔧 手动切换
🇯🇵 日本 = select,🇯🇵 日本最佳,🇯🇵 日本均衡,🔧 手动切换
🇺🇸 美国 = select,🇺🇸 美国最佳,🇺🇸 美国均衡,🔧 手动切换
🇸🇬 狮城 = select,🇸🇬 狮城最佳,🇸🇬 狮城均衡,🔧 手动切换
🇬🇧 英国 = select,🇬🇧 英国最佳,🇬🇧 英国均衡,🔧 手动切换
🇨🇳 台湾 = select,🇨🇳 台湾最佳,🇨🇳 台湾均衡,🔧 手动切换
———————自动——————— = select,DIRECT
🇭🇰 香港最佳 = url-test,{proxies_one_line_hk},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50
🇯🇵 日本最佳 = url-test,{proxies_one_line_jp},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50
🇺🇸 美国最佳 = url-test,{proxies_one_line_us},url=http://www.github.com,interval=300,tolerance=50
🇸🇬 狮城最佳 = url-test,{proxies_one_line_sg},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50
🇬🇧 英国最佳 = url-test,{proxies_one_line_gb},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50
🇨🇳 台湾最佳 = url-test,{proxies_one_line_tw},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50
🇭🇰 香港均衡 = load-balance,{proxies_one_line_hk}, persistent=1
🇯🇵 日本均衡 = load-balance,{proxies_one_line_jp}, persistent=1
🇺🇸 美国均衡 = load-balance,{proxies_one_line_us}, persistent=1
🇸🇬 狮城均衡 = load-balance,{proxies_one_line_sg}, persistent=1
🇬🇧 英国均衡 = load-balance,{proxies_one_line_gb}, persistent=1
🇨🇳 台湾均衡 = load-balance,{proxies_one_line_tw}, persistent=1

[Rule]
DOMAIN-SUFFIX,youtube.com,🚀 节点选择
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
GEOIP,CN,🎯 全球直连
FINAL,🐟 漏网之鱼
"""
)

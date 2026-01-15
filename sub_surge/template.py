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


clash_template = ( # use yaml to load: import yaml; config = yaml.load(clash_template, Loader=yaml.FullLoader)
"""
port: 7890
socks-port: 7891
allow-lan: true
mode: Rule
log-level: info
external-controller: :9090
sniffer:
    sniff:
        TLS:
            ports:
            - 1-65535
            override-destination: true
        HTTP:
            ports:
            - 1-65535
            override-destination: true
    enable: true
    skip-domain:
    - Mijia Cloud
    - dlg.io.mi.com
    parse-pure-ip: true
    force-dns-mapping: true
    override-destination: true
dns:
    ipv6: false
    enable: true
    listen: 0.0.0.0:1053
    use-hosts: false
    default-nameserver:
    - 119.28.28.28
    - 119.29.29.29
    - 223.5.5.5
    - 223.6.6.6
    nameserver:
    - 119.29.29.29
    - 223.5.5.5
    - tls://dot.pub:853
    - tls://dns.alidns.com:853
    - https://doh.pub:443/dns-query
    - https://dns.alidns.com:443/dns-query
    fake-ip-range: 198.18.0.1/15
    fake-ip-filter:
    - '*.lan'
    - '*.localdomain'
    - '*.example'
    - '*.invalid'
    - '*.localhost'
    - '*.test'
    - '*.local'
    - '*.home.arpa'
    - time.*.com
    - time.*.gov
    - time.*.edu.cn
    - time.*.apple.com
    - time1.*.com
    - time2.*.com
    - time3.*.com
    - time4.*.com
    - time5.*.com
    - time6.*.com
    - time7.*.com
    - ntp.*.com
    - ntp1.*.com
    - ntp2.*.com
    - ntp3.*.com
    - ntp4.*.com
    - ntp5.*.com
    - ntp6.*.com
    - ntp7.*.com
    - '*.time.edu.cn'
    - '*.ntp.org.cn'
    - +.pool.ntp.org
    - time1.cloud.tencent.com
    - stun.*.*
    - stun.*.*.*
    - swscan.apple.com
    - mesu.apple.com
    - music.163.com
    - '*.music.163.com'
    - '*.126.net'
    - musicapi.taihe.com
    - music.taihe.com
    - songsearch.kugou.com
    - trackercdn.kugou.com
    - '*.kuwo.cn'
    - api-jooxtt.sanook.com
    - api.joox.com
    - y.qq.com
    - '*.y.qq.com'
    - streamoc.music.tc.qq.com
    - mobileoc.music.tc.qq.com
    - isure.stream.qqmusic.qq.com
    - dl.stream.qqmusic.qq.com
    - aqqmusic.tc.qq.com
    - amobile.music.tc.qq.com
    - localhost.ptlogin2.qq.com
    - '*.msftconnecttest.com'
    - '*.msftncsi.com'
    - '*.xiami.com'
    - '*.music.migu.cn'
    - music.migu.cn
    - +.wotgame.cn
    - +.wggames.cn
    - +.wowsgame.cn
    - +.wargaming.net
    - '*.*.*.srv.nintendo.net'
    - '*.*.stun.playstation.net'
    - xbox.*.*.microsoft.com
    - '*.*.xboxlive.com'
    - '*.ipv6.microsoft.com'
    - teredo.*.*.*
    - teredo.*.*
    - speedtest.cros.wr.pvp.net
    - +.jjvip8.com
    - www.douyu.com
    - activityapi.huya.com
    - activityapi.huya.com.w.cdngslb.com
    - www.bilibili.com
    - api.bilibili.com
    - a.w.bilicdn1.com
proxies:
proxy-groups:
-   name: 🚀 节点选择
    type: select
    proxies:
    - ♻️ 自动选择
    - 🚀 手动切换
    - 🇭🇰 香港
    - 🇯🇵 日本
    - 🇸🇬 狮城
    - 🇨🇳 台湾
    - 🇬🇧 英国
    - 🇺🇸 美国
-   name: 🚀 手动切换
    type: select
    proxies:
    - ♻️ 自动选择
-   name: ♻️ 自动选择
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    proxies:
rules:
- GEOIP,CN,🎯 全球直连
- MATCH,🐟 漏网之鱼
host:
"""
)

clash_proxy_template = {
    'name': '',
    'server': '',
    'port': 0,
    'type': '',
    'cipher': '',
    'password': '',
    'udp': True
}

clash_proxy_group_template = {
    'name': '',
    'type': '', # 'select', 'url-test', 'load-balance'
    # if type == 'url-test'
        # 'url': 'http://www.gstatic.com/generate_204',
        # 'interval': 300,
        # 'tolerance': 50
    # elif type == 'load-balance'
        # 'strategy': 'consistent-hashing'
        # 'url': 'http://www.gstatic.com/generate_204',
        # 'interval': 300,
    'proxies': []
}
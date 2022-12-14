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

[Script]
http-request https?:\/\/.*\.iqiyi\.com\/.*authcookie= script-path=https://raw.githubusercontent.com/NobyDa/Script/master/iQIYI-DailyBonus/iQIYI.js

[Proxy]
DIRECT = direct
{proxies}

[Proxy Group]
๐ ๆบๅบไฟกๆฏ = select,{infos}
๐ ่็น้ๆฉ = select,DIRECT,๐ง ๆๅจๅๆข,๐ญ๐ฐ ้ฆๆธฏ่็น,๐ฏ๐ต ๆฅๆฌๆไฝณ,๐บ๐ธ ็พๅฝๆไฝณ,๐ธ๐ฌ ็ฎๅๆไฝณ
๐ง ๆๅจๅๆข = select,DIRECT,{proxies_one_line}
๐ ๅฝๅคๅชไฝ = select,๐ ่็น้ๆฉ,๐ฏ ๅจ็็ด่ฟ,๐ธ๐ฌ ็ฎๅๆไฝณ,๐บ๐ธ ็พๅฝๆไฝณ
๐ฒ ็ตๆฅไฟกๆฏ = select,๐ ่็น้ๆฉ,๐ฏ ๅจ็็ด่ฟ,{proxies_one_line}
โ๏ธ ๅพฎ่ฝฏๆๅก = select,๐ฏ ๅจ็็ด่ฟ,๐ ่็น้ๆฉ,{proxies_one_line}
๐ ่นๆๆๅก = select,๐ ่็น้ๆฉ,๐ฏ ๅจ็็ด่ฟ,{proxies_one_line}
๐ข ่ฐทๆญFCM = select,๐ ่็น้ๆฉ,๐ฏ ๅจ็็ด่ฟ,{proxies_one_line}
๐ฏ ๅจ็็ด่ฟ = select,DIRECT,๐ ่็น้ๆฉ
๐ ๅจ็ๆฆๆช = select,REJECT,DIRECT
๐ ๅบ็จๅๅ = select,REJECT,DIRECT
๐ ๆผ็ฝไน้ฑผ = select,๐ ่็น้ๆฉ,๐ฏ ๅจ็็ด่ฟ,{proxies_one_line}
๐ญ๐ฐ ้ฆๆธฏ่็น = url-test,{proxies_one_line_hk},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50
๐ฏ๐ต ๆฅๆฌๆไฝณ = url-test,{proxies_one_line_jp},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50
๐บ๐ธ ็พๅฝๆไฝณ = url-test,{proxies_one_line_us},url=http://www.github.com,interval=300,tolerance=50
๐ธ๐ฌ ็ฎๅๆไฝณ = url-test,{proxies_one_line_sg},url=http://www.gstatic.com/generate_204,interval=300,tolerance=50

[Rule]
DOMAIN-SUFFIX,youtube.com,๐ ่็น้ๆฉ
DOMAIN-SUFFIX,jp,๐ฏ๐ต ๆฅๆฌๆไฝณ
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/LocalAreaNetwork.list,๐ฏ ๅจ็็ด่ฟ,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/UnBan.list,๐ฏ ๅจ็็ด่ฟ,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanAD.list,๐ ๅจ็ๆฆๆช,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanProgramAD.list,๐ ๅบ็จๅๅ,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/GoogleFCM.list,๐ข ่ฐทๆญFCM,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/GoogleCN.list,๐ฏ ๅจ็็ด่ฟ,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/SteamCN.list,๐ฏ ๅจ็็ด่ฟ,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Microsoft.list,โ๏ธ ๅพฎ่ฝฏๆๅก,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Apple.list,๐ ่นๆๆๅก,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Telegram.list,๐ฒ ็ตๆฅไฟกๆฏ,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ProxyMedia.list,๐ ๅฝๅคๅชไฝ,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ProxyLite.list,๐ ่็น้ๆฉ,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaDomain.list,๐ฏ ๅจ็็ด่ฟ,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaCompanyIp.list,๐ฏ ๅจ็็ด่ฟ,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/Rhythmicc/ACL4SSR/master/Clash/us.list,๐บ๐ธ ็พๅฝๆไฝณ,update-interval=86400
RULE-SET,https://raw.githubusercontent.com/Rhythmicc/ACL4SSR/master/Clash/direct.list,DIRECT,update-interval=86400
GEOIP,CN,๐ฏ ๅจ็็ด่ฟ
FINAL,๐ ๆผ็ฝไน้ฑผ
"""
)

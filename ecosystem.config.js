const path = require('path');
const os = require('os');

// 提取路径逻辑：如果有环境变量则使用，否则默认为用户主目录下的 .sub-surge
const configDir = process.env.SUB_SURGE_CONFIG_DIR || path.join(os.homedir(), '.sub-surge');

module.exports = {
  apps: [
    {
      name: 'sub-surge',
      script: 'sub-surge',
      args: 'serve',
      interpreter: 'none',
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '500M',
      error_file: path.join(configDir, 'logs', 'pm2-error.log'),
      out_file: path.join(configDir, 'logs', 'pm2-out.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      listen_timeout: 3000,
      kill_timeout: 5000,
      env: {
        NODE_ENV: 'production',
        SUB_SURGE_CONFIG_DIR: configDir,
        PYTHONUNBUFFERED: '1'
      }
    }
  ]
};

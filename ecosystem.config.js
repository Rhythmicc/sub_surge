module.exports = {
  apps: [
    {
      name: 'sub-surge',
      script: 'sub-surge',
      args: 'serve',
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '500M',
      error_file: process.env.SUB_SURGE_CONFIG_DIR 
        ? `${process.env.SUB_SURGE_CONFIG_DIR}/logs/pm2-error.log`
        : `${process.env.HOME}/.sub-surge/logs/pm2-error.log`,
      out_file: process.env.SUB_SURGE_CONFIG_DIR
        ? `${process.env.SUB_SURGE_CONFIG_DIR}/logs/pm2-out.log`
        : `${process.env.HOME}/.sub-surge/logs/pm2-out.log`,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      listen_timeout: 3000,
      kill_timeout: 5000,
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
};

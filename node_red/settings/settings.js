/**
 * FactoryPulse AI - Node-RED Runtime Settings
 */

module.exports = {
    uiPort: process.env.PORT || 1880,
    mqttReconnectTime: 5000,
    serialReconnectTime: 15000,
    debugMaxLength: 1000,
    flowFile: '../flows.json',
    flowFilePretty: true,
    credentialSecret: 'factorypulse-secret-key-2026',
    adminAuth: null,
    logging: {
        console: {
            level: "info",
            metrics: false,
            audit: false
        }
    },
    exportGlobalContextKeys: false,
    externalModules: {
        autoInstall: true
    },
    editorTheme: {
        header: {
            title: "FactoryPulse AI — Production Alerting Engine",
            image: null
        },
        deployButton: {
            type: "default",
            label: "Deploy Flow"
        }
    }
};


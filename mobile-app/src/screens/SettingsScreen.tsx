import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import {
  Card,
  Button,
  TextInput,
  Switch,
  List,
  Divider,
} from 'react-native-paper';
import { showMessage } from 'react-native-flash-message';

import { apiService, BotConfig } from '../services/api';
import { useWebSocket } from '../context/WebSocketContext';

const SettingsScreen: React.FC = () => {
  const { botStatus, isConnected } = useWebSocket();
  const [config, setConfig] = useState<BotConfig>({
    symbols: ['EURUSDm', 'XAUUSDm'],
    risk_per_trade: 0.02,
    max_drawdown: 0.1,
    stop_loss: 50,
    take_profit: 100,
  });
  const [loading, setLoading] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [autoTrading, setAutoTrading] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await apiService.getBotConfig();
      if (response.data) {
        setConfig({
          symbols: response.data.symbols || [],
          risk_per_trade: response.data.risk_parameters?.risk_per_trade || 0.02,
          max_drawdown: response.data.risk_parameters?.max_drawdown || 0.1,
          stop_loss: response.data.risk_parameters?.stop_loss || 50,
          take_profit: response.data.risk_parameters?.take_profit || 100,
        });
      }
    } catch (error) {
      showMessage({
        message: 'Failed to load configuration',
        type: 'danger',
      });
    }
  };

  const saveConfig = async () => {
    try {
      setLoading(true);
      await apiService.updateBotConfig(config);
      showMessage({
        message: 'Configuration saved successfully',
        type: 'success',
      });
    } catch (error) {
      showMessage({
        message: 'Failed to save configuration',
        type: 'danger',
      });
    } finally {
      setLoading(false);
    }
  };

  const resetConfig = () => {
    Alert.alert(
      'Reset Configuration',
      'Are you sure you want to reset all settings to default values?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: () => {
            setConfig({
              symbols: ['EURUSDm', 'XAUUSDm'],
              risk_per_trade: 0.02,
              max_drawdown: 0.1,
              stop_loss: 50,
              take_profit: 100,
            });
            showMessage({
              message: 'Configuration reset to defaults',
              type: 'info',
            });
          },
        },
      ]
    );
  };

  const exportLogs = () => {
    showMessage({
      message: 'Export logs feature coming soon',
      type: 'info',
    });
  };

  const clearData = () => {
    Alert.alert(
      'Clear Data',
      'This will clear all trade history and logs. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: () => {
            showMessage({
              message: 'Clear data feature coming soon',
              type: 'info',
            });
          },
        },
      ]
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Connection Status */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Connection Status</Text>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Server Connection:</Text>
              <Text style={[
                styles.statusValue,
                { color: isConnected ? '#4CAF50' : '#f44336' }
              ]}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </Text>
            </View>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Bot Status:</Text>
              <Text style={[
                styles.statusValue,
                { color: botStatus.running ? '#4CAF50' : '#f44336' }
              ]}>
                {botStatus.running ? 'Running' : 'Stopped'}
              </Text>
            </View>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>MT5 Connection:</Text>
              <Text style={[
                styles.statusValue,
                { color: botStatus.connected ? '#4CAF50' : '#f44336' }
              ]}>
                {botStatus.connected ? 'Connected' : 'Disconnected'}
              </Text>
            </View>
          </Card.Content>
        </Card>

        {/* Trading Configuration */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Trading Configuration</Text>
            
            <TextInput
              label="Risk Per Trade (%)"
              value={(config.risk_per_trade * 100).toString()}
              onChangeText={(text) => setConfig({
                ...config,
                risk_per_trade: parseFloat(text) / 100 || 0.02
              })}
              keyboardType="numeric"
              style={styles.input}
              theme={{ colors: { primary: '#4CAF50' } }}
            />

            <TextInput
              label="Max Drawdown (%)"
              value={(config.max_drawdown * 100).toString()}
              onChangeText={(text) => setConfig({
                ...config,
                max_drawdown: parseFloat(text) / 100 || 0.1
              })}
              keyboardType="numeric"
              style={styles.input}
              theme={{ colors: { primary: '#4CAF50' } }}
            />

            <TextInput
              label="Stop Loss (pips)"
              value={config.stop_loss.toString()}
              onChangeText={(text) => setConfig({
                ...config,
                stop_loss: parseInt(text) || 50
              })}
              keyboardType="numeric"
              style={styles.input}
              theme={{ colors: { primary: '#4CAF50' } }}
            />

            <TextInput
              label="Take Profit (pips)"
              value={config.take_profit.toString()}
              onChangeText={(text) => setConfig({
                ...config,
                take_profit: parseInt(text) || 100
              })}
              keyboardType="numeric"
              style={styles.input}
              theme={{ colors: { primary: '#4CAF50' } }}
            />

            <View style={styles.buttonRow}>
              <Button
                mode="contained"
                onPress={saveConfig}
                loading={loading}
                disabled={loading}
                style={[styles.button, { backgroundColor: '#4CAF50' }]}
                labelStyle={{ color: 'white' }}
              >
                Save Config
              </Button>
              <Button
                mode="outlined"
                onPress={resetConfig}
                style={[styles.button, { borderColor: '#f44336' }]}
                labelStyle={{ color: '#f44336' }}
              >
                Reset
              </Button>
            </View>
          </Card.Content>
        </Card>

        {/* App Settings */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>App Settings</Text>
            
            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Push Notifications</Text>
              <Switch
                value={notifications}
                onValueChange={setNotifications}
                color="#4CAF50"
              />
            </View>
            
            <Divider style={styles.divider} />
            
            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Auto Trading</Text>
              <Switch
                value={autoTrading}
                onValueChange={setAutoTrading}
                color="#4CAF50"
              />
            </View>
          </Card.Content>
        </Card>

        {/* Data Management */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Data Management</Text>
            
            <List.Item
              title="Export Logs"
              description="Export trading logs and performance data"
              titleStyle={{ color: '#fff' }}
              descriptionStyle={{ color: '#888' }}
              left={(props) => <List.Icon {...props} icon="download" color="#4CAF50" />}
              onPress={exportLogs}
              style={styles.listItem}
            />
            
            <List.Item
              title="Clear Data"
              description="Clear all trade history and logs"
              titleStyle={{ color: '#f44336' }}
              descriptionStyle={{ color: '#888' }}
              left={(props) => <List.Icon {...props} icon="delete" color="#f44336" />}
              onPress={clearData}
              style={styles.listItem}
            />
          </Card.Content>
        </Card>

        {/* App Information */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>App Information</Text>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Version:</Text>
              <Text style={styles.infoValue}>1.0.0</Text>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Build:</Text>
              <Text style={styles.infoValue}>2024.01.01</Text>
            </View>
            
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>API Version:</Text>
              <Text style={styles.infoValue}>v1.0.0</Text>
            </View>
          </Card.Content>
        </Card>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f23',
  },
  content: {
    padding: 20,
  },
  card: {
    marginBottom: 20,
    backgroundColor: '#1a1a2e',
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  statusLabel: {
    color: '#ccc',
    fontSize: 16,
  },
  statusValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  input: {
    marginBottom: 15,
    backgroundColor: '#16213e',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
  },
  button: {
    flex: 1,
    marginHorizontal: 5,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  settingLabel: {
    color: '#fff',
    fontSize: 16,
  },
  divider: {
    backgroundColor: '#333',
    marginVertical: 10,
  },
  listItem: {
    paddingHorizontal: 0,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  infoLabel: {
    color: '#ccc',
    fontSize: 16,
  },
  infoValue: {
    color: '#fff',
    fontSize: 16,
  },
});

export default SettingsScreen;
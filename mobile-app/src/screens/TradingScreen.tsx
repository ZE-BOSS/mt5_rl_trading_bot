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
  Chip,
  Modal,
  Portal,
  ActivityIndicator,
} from 'react-native-paper';
import RNPickerSelect from 'react-native-picker-select';
import { showMessage } from 'react-native-flash-message';

import { apiService, TradeRequest } from '../services/api';
import { useWebSocket } from '../context/WebSocketContext';

const SYMBOLS = [
  { label: 'EUR/USD', value: 'EURUSDm' },
  { label: 'GBP/USD', value: 'GBPUSDm' },
  { label: 'XAU/USD (Gold)', value: 'XAUUSDm' },
  { label: 'GBP/JPY', value: 'GBPJPYm' },
  { label: 'XAG/USD (Silver)', value: 'XAGUSDm' },
  { label: 'US30', value: 'US30' },
  { label: 'NAS100', value: 'NAS100' },
  { label: 'BTC/USD', value: 'BTCUSDm' },
  { label: 'ETH/USD', value: 'ETHUSDm' },
  { label: 'USD/JPY', value: 'USDJPYm' },
];

const TradingScreen: React.FC = () => {
  const { botStatus, isConnected } = useWebSocket();
  const [selectedSymbol, setSelectedSymbol] = useState('EURUSDm');
  const [volume, setVolume] = useState('0.01');
  const [stopLoss, setStopLoss] = useState('');
  const [takeProfit, setTakeProfit] = useState('');
  const [marketData, setMarketData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [tradeModalVisible, setTradeModalVisible] = useState(false);
  const [tradeAction, setTradeAction] = useState<'buy' | 'sell'>('buy');

  useEffect(() => {
    loadMarketData();
  }, [selectedSymbol]);

  const loadMarketData = async () => {
    try {
      setLoading(true);
      const response = await apiService.getMarketData(selectedSymbol, 50);
      setMarketData(response.data);
    } catch (error) {
      showMessage({
        message: 'Failed to load market data',
        type: 'danger',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTrade = (action: 'buy' | 'sell') => {
    setTradeAction(action);
    setTradeModalVisible(true);
  };

  const executeTrade = async () => {
    try {
      if (!volume || parseFloat(volume) <= 0) {
        showMessage({
          message: 'Please enter a valid volume',
          type: 'warning',
        });
        return;
      }

      const tradeRequest: TradeRequest = {
        symbol: selectedSymbol,
        action: tradeAction,
        volume: parseFloat(volume),
        stop_loss: stopLoss ? parseFloat(stopLoss) : undefined,
        take_profit: takeProfit ? parseFloat(takeProfit) : undefined,
      };

      await apiService.executeTrade(tradeRequest);
      setTradeModalVisible(false);
      showMessage({
        message: `${tradeAction.toUpperCase()} order executed successfully`,
        type: 'success',
      });
    } catch (error) {
      showMessage({
        message: 'Failed to execute trade',
        type: 'danger',
      });
    }
  };

  const getCurrentPrice = () => {
    if (!marketData?.data || marketData.data.length === 0) return null;
    const latestData = marketData.data[marketData.data.length - 1];
    return latestData.close;
  };

  const getPriceChange = () => {
    if (!marketData?.data || marketData.data.length < 2) return { change: 0, percentage: 0 };
    const data = marketData.data;
    const current = data[data.length - 1].close;
    const previous = data[data.length - 2].close;
    const change = current - previous;
    const percentage = (change / previous) * 100;
    return { change, percentage };
  };

  const currentPrice = getCurrentPrice();
  const priceChange = getPriceChange();

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Symbol Selection */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Select Symbol</Text>
            <View style={styles.pickerContainer}>
              <RNPickerSelect
                onValueChange={setSelectedSymbol}
                items={SYMBOLS}
                value={selectedSymbol}
                style={pickerSelectStyles}
                placeholder={{}}
              />
            </View>
          </Card.Content>
        </Card>

        {/* Market Data */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Market Data</Text>
            {loading ? (
              <ActivityIndicator size="small" color="#4CAF50" />
            ) : (
              <View>
                <View style={styles.priceContainer}>
                  <Text style={styles.priceLabel}>Current Price:</Text>
                  <Text style={styles.priceValue}>
                    {currentPrice?.toFixed(5) || 'N/A'}
                  </Text>
                </View>
                <View style={styles.priceChangeContainer}>
                  <Text style={styles.priceChangeLabel}>Change:</Text>
                  <Text
                    style={[
                      styles.priceChangeValue,
                      { color: priceChange.change >= 0 ? '#4CAF50' : '#f44336' },
                    ]}
                  >
                    {priceChange.change >= 0 ? '+' : ''}
                    {priceChange.change.toFixed(5)} ({priceChange.percentage.toFixed(2)}%)
                  </Text>
                </View>
                <Button
                  mode="outlined"
                  onPress={loadMarketData}
                  style={styles.refreshButton}
                  labelStyle={{ color: '#4CAF50' }}
                >
                  Refresh Data
                </Button>
              </View>
            )}
          </Card.Content>
        </Card>

        {/* Bot Status */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Bot Status</Text>
            <View style={styles.statusContainer}>
              <Chip
                mode="outlined"
                textStyle={{ color: isConnected ? '#4CAF50' : '#f44336' }}
                style={{
                  borderColor: isConnected ? '#4CAF50' : '#f44336',
                  marginRight: 10,
                }}
              >
                {isConnected ? 'Connected' : 'Disconnected'}
              </Chip>
              <Chip
                mode="outlined"
                textStyle={{ color: botStatus.running ? '#4CAF50' : '#f44336' }}
                style={{
                  borderColor: botStatus.running ? '#4CAF50' : '#f44336',
                }}
              >
                {botStatus.running ? 'Running' : 'Stopped'}
              </Chip>
            </View>
          </Card.Content>
        </Card>

        {/* Manual Trading */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Manual Trading</Text>
            
            <TextInput
              label="Volume"
              value={volume}
              onChangeText={setVolume}
              keyboardType="numeric"
              style={styles.input}
              theme={{ colors: { primary: '#4CAF50' } }}
            />

            <TextInput
              label="Stop Loss (Optional)"
              value={stopLoss}
              onChangeText={setStopLoss}
              keyboardType="numeric"
              style={styles.input}
              theme={{ colors: { primary: '#4CAF50' } }}
            />

            <TextInput
              label="Take Profit (Optional)"
              value={takeProfit}
              onChangeText={setTakeProfit}
              keyboardType="numeric"
              style={styles.input}
              theme={{ colors: { primary: '#4CAF50' } }}
            />

            <View style={styles.tradeButtons}>
              <Button
                mode="contained"
                onPress={() => handleTrade('buy')}
                style={[styles.tradeButton, { backgroundColor: '#4CAF50' }]}
                labelStyle={{ color: 'white' }}
                disabled={!isConnected}
              >
                BUY
              </Button>
              <Button
                mode="contained"
                onPress={() => handleTrade('sell')}
                style={[styles.tradeButton, { backgroundColor: '#f44336' }]}
                labelStyle={{ color: 'white' }}
                disabled={!isConnected}
              >
                SELL
              </Button>
            </View>
          </Card.Content>
        </Card>
      </View>

      {/* Trade Confirmation Modal */}
      <Portal>
        <Modal
          visible={tradeModalVisible}
          onDismiss={() => setTradeModalVisible(false)}
          contentContainerStyle={styles.modal}
        >
          <Text style={styles.modalTitle}>Confirm Trade</Text>
          <Text style={styles.modalText}>
            {tradeAction.toUpperCase()} {volume} lots of {selectedSymbol}
          </Text>
          {currentPrice && (
            <Text style={styles.modalText}>
              Current Price: {currentPrice.toFixed(5)}
            </Text>
          )}
          {stopLoss && (
            <Text style={styles.modalText}>Stop Loss: {stopLoss}</Text>
          )}
          {takeProfit && (
            <Text style={styles.modalText}>Take Profit: {takeProfit}</Text>
          )}
          
          <View style={styles.modalButtons}>
            <Button
              mode="outlined"
              onPress={() => setTradeModalVisible(false)}
              style={styles.modalButton}
            >
              Cancel
            </Button>
            <Button
              mode="contained"
              onPress={executeTrade}
              style={[styles.modalButton, { backgroundColor: '#4CAF50' }]}
              labelStyle={{ color: 'white' }}
            >
              Confirm
            </Button>
          </View>
        </Modal>
      </Portal>
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
  pickerContainer: {
    backgroundColor: '#16213e',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333',
  },
  priceContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  priceLabel: {
    color: '#ccc',
    fontSize: 16,
  },
  priceValue: {
    color: '#4CAF50',
    fontSize: 18,
    fontWeight: 'bold',
  },
  priceChangeContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  priceChangeLabel: {
    color: '#ccc',
    fontSize: 16,
  },
  priceChangeValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  refreshButton: {
    borderColor: '#4CAF50',
  },
  statusContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  input: {
    marginBottom: 15,
    backgroundColor: '#16213e',
  },
  tradeButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
  },
  tradeButton: {
    flex: 1,
    marginHorizontal: 5,
  },
  modal: {
    backgroundColor: '#1a1a2e',
    padding: 20,
    margin: 20,
    borderRadius: 10,
  },
  modalTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
    textAlign: 'center',
  },
  modalText: {
    color: '#ccc',
    fontSize: 16,
    marginBottom: 10,
    textAlign: 'center',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
  },
  modalButton: {
    flex: 1,
    marginHorizontal: 5,
  },
});

const pickerSelectStyles = StyleSheet.create({
  inputIOS: {
    fontSize: 16,
    paddingVertical: 12,
    paddingHorizontal: 10,
    color: '#fff',
    paddingRight: 30,
  },
  inputAndroid: {
    fontSize: 16,
    paddingHorizontal: 10,
    paddingVertical: 8,
    color: '#fff',
    paddingRight: 30,
  },
});

export default TradingScreen;
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Dimensions,
} from 'react-native';
import {
  Card,
  Button,
  TextInput,
  ActivityIndicator,
  DataTable,
} from 'react-native-paper';
import { LineChart } from 'react-native-chart-kit';
import RNPickerSelect from 'react-native-picker-select';
import { showMessage } from 'react-native-flash-message';

import { apiService, BacktestRequest } from '../services/api';

const screenWidth = Dimensions.get('window').width;

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

const BacktestScreen: React.FC = () => {
  const [symbol, setSymbol] = useState('XAUUSDm');
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [episodes, setEpisodes] = useState('100');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);

  const runBacktest = async () => {
    try {
      if (!startDate || !endDate) {
        showMessage({
          message: 'Please enter valid start and end dates',
          type: 'warning',
        });
        return;
      }

      setLoading(true);
      const request: BacktestRequest = {
        symbol,
        start_date: startDate,
        end_date: endDate,
        episodes: parseInt(episodes) || 100,
      };

      const response = await apiService.runBacktest(request);
      setResults(response.data);
      showMessage({
        message: 'Backtest completed successfully',
        type: 'success',
      });
    } catch (error) {
      showMessage({
        message: 'Backtest failed',
        type: 'danger',
      });
    } finally {
      setLoading(false);
    }
  };

  const getEquityCurveData = () => {
    if (!results?.results || results.results.length === 0) {
      return {
        labels: ['Start'],
        datasets: [{ data: [10000] }],
      };
    }

    const labels = [];
    const data = [];
    let balance = 10000;

    results.results.forEach((trade: any, index: number) => {
      if (index % 10 === 0 || index === results.results.length - 1) {
        labels.push(`T${index + 1}`);
        balance = trade.balance_after || balance;
        data.push(balance);
      }
    });

    return {
      labels,
      datasets: [
        {
          data,
          color: (opacity = 1) => `rgba(76, 175, 80, ${opacity})`,
          strokeWidth: 2,
        },
      ],
    };
  };

  const chartConfig = {
    backgroundColor: '#1a1a2e',
    backgroundGradientFrom: '#1a1a2e',
    backgroundGradientTo: '#16213e',
    decimalPlaces: 0,
    color: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
    style: {
      borderRadius: 16,
    },
    propsForDots: {
      r: '4',
      strokeWidth: '2',
      stroke: '#4CAF50',
    },
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Backtest Configuration */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Backtest Configuration</Text>
            
            <Text style={styles.inputLabel}>Symbol</Text>
            <View style={styles.pickerContainer}>
              <RNPickerSelect
                onValueChange={setSymbol}
                items={SYMBOLS}
                value={symbol}
                style={pickerSelectStyles}
                placeholder={{}}
              />
            </View>

            <TextInput
              label="Start Date (YYYY-MM-DD)"
              value={startDate}
              onChangeText={setStartDate}
              style={styles.input}
              theme={{ colors: { primary: '#4CAF50' } }}
            />

            <TextInput
              label="End Date (YYYY-MM-DD)"
              value={endDate}
              onChangeText={setEndDate}
              style={styles.input}
              theme={{ colors: { primary: '#4CAF50' } }}
            />

            <TextInput
              label="Training Episodes"
              value={episodes}
              onChangeText={setEpisodes}
              keyboardType="numeric"
              style={styles.input}
              theme={{ colors: { primary: '#4CAF50' } }}
            />

            <Button
              mode="contained"
              onPress={runBacktest}
              loading={loading}
              disabled={loading}
              style={styles.runButton}
              labelStyle={{ color: 'white' }}
            >
              {loading ? 'Running Backtest...' : 'Run Backtest'}
            </Button>
          </Card.Content>
        </Card>

        {/* Results Summary */}
        {results && (
          <Card style={styles.card}>
            <Card.Content>
              <Text style={styles.sectionTitle}>Backtest Results</Text>
              
              <View style={styles.summaryGrid}>
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryLabel}>Total Trades</Text>
                  <Text style={styles.summaryValue}>
                    {results.summary?.total_trades || 0}
                  </Text>
                </View>
                
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryLabel}>Final Balance</Text>
                  <Text style={[
                    styles.summaryValue,
                    { color: results.summary?.final_balance >= 10000 ? '#4CAF50' : '#f44336' }
                  ]}>
                    ${results.summary?.final_balance?.toFixed(2) || '0.00'}
                  </Text>
                </View>
                
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryLabel}>Total Return</Text>
                  <Text style={[
                    styles.summaryValue,
                    { color: results.summary?.total_return >= 0 ? '#4CAF50' : '#f44336' }
                  ]}>
                    {results.summary?.total_return >= 0 ? '+' : ''}
                    ${results.summary?.total_return?.toFixed(2) || '0.00'}
                  </Text>
                </View>
                
                <View style={styles.summaryItem}>
                  <Text style={styles.summaryLabel}>Max Drawdown</Text>
                  <Text style={[styles.summaryValue, { color: '#f44336' }]}>
                    ${results.summary?.max_drawdown?.toFixed(2) || '0.00'}
                  </Text>
                </View>
              </View>
            </Card.Content>
          </Card>
        )}

        {/* Equity Curve Chart */}
        {results && (
          <Card style={styles.card}>
            <Card.Content>
              <Text style={styles.sectionTitle}>Equity Curve</Text>
              <LineChart
                data={getEquityCurveData()}
                width={screenWidth - 60}
                height={220}
                chartConfig={chartConfig}
                bezier
                style={styles.chart}
              />
            </Card.Content>
          </Card>
        )}

        {/* Trade Details */}
        {results && results.results && results.results.length > 0 && (
          <Card style={styles.card}>
            <Card.Content>
              <Text style={styles.sectionTitle}>Recent Trades</Text>
              <DataTable>
                <DataTable.Header>
                  <DataTable.Title textStyle={{ color: '#fff' }}>Entry</DataTable.Title>
                  <DataTable.Title textStyle={{ color: '#fff' }}>Exit</DataTable.Title>
                  <DataTable.Title textStyle={{ color: '#fff' }}>P&L</DataTable.Title>
                  <DataTable.Title textStyle={{ color: '#fff' }}>Balance</DataTable.Title>
                </DataTable.Header>

                {results.results.slice(-5).map((trade: any, index: number) => (
                  <DataTable.Row key={index}>
                    <DataTable.Cell textStyle={{ color: '#ccc' }}>
                      {trade.entry_price?.toFixed(5) || 'N/A'}
                    </DataTable.Cell>
                    <DataTable.Cell textStyle={{ color: '#ccc' }}>
                      {trade.exit_price?.toFixed(5) || 'N/A'}
                    </DataTable.Cell>
                    <DataTable.Cell textStyle={{
                      color: trade.outcome >= 0 ? '#4CAF50' : '#f44336'
                    }}>
                      {trade.outcome >= 0 ? '+' : ''}
                      {trade.outcome?.toFixed(2) || '0.00'}
                    </DataTable.Cell>
                    <DataTable.Cell textStyle={{ color: '#ccc' }}>
                      ${trade.balance_after?.toFixed(2) || '0.00'}
                    </DataTable.Cell>
                  </DataTable.Row>
                ))}
              </DataTable>
            </Card.Content>
          </Card>
        )}

        {loading && (
          <Card style={styles.card}>
            <Card.Content style={styles.loadingContent}>
              <ActivityIndicator size="large" color="#4CAF50" />
              <Text style={styles.loadingText}>
                Running backtest... This may take a few minutes.
              </Text>
            </Card.Content>
          </Card>
        )}
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
  inputLabel: {
    color: '#ccc',
    fontSize: 14,
    marginBottom: 5,
    marginTop: 10,
  },
  pickerContainer: {
    backgroundColor: '#16213e',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333',
    marginBottom: 15,
  },
  input: {
    marginBottom: 15,
    backgroundColor: '#16213e',
  },
  runButton: {
    backgroundColor: '#4CAF50',
    marginTop: 10,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  summaryItem: {
    width: '48%',
    marginBottom: 15,
  },
  summaryLabel: {
    color: '#888',
    fontSize: 12,
    marginBottom: 5,
  },
  summaryValue: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  loadingContent: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    color: '#ccc',
    marginTop: 10,
    textAlign: 'center',
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

export default BacktestScreen;
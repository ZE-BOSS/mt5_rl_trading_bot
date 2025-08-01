import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { Card, Button, Chip, ActivityIndicator } from 'react-native-paper';
import { LineChart } from 'react-native-chart-kit';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

import { useWebSocket } from '../context/WebSocketContext';
import { apiService } from '../services/api';
import { showMessage } from 'react-native-flash-message';

const screenWidth = Dimensions.get('window').width;

const DashboardScreen: React.FC = () => {
  const { isConnected, botStatus } = useWebSocket();
  const [performance, setPerformance] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadPerformanceData();
  }, []);

  const loadPerformanceData = async () => {
    try {
      setLoading(true);
      const response = await apiService.getPerformance();
      setPerformance(response.data);
    } catch (error) {
      showMessage({
        message: 'Failed to load performance data',
        type: 'danger',
      });
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadPerformanceData();
    setRefreshing(false);
  };

  const handleStartBot = async () => {
    try {
      await apiService.startBot();
      showMessage({
        message: 'Bot started successfully',
        type: 'success',
      });
    } catch (error) {
      showMessage({
        message: 'Failed to start bot',
        type: 'danger',
      });
    }
  };

  const handleStopBot = async () => {
    try {
      await apiService.stopBot();
      showMessage({
        message: 'Bot stopped successfully',
        type: 'success',
      });
    } catch (error) {
      showMessage({
        message: 'Failed to stop bot',
        type: 'danger',
      });
    }
  };

  // Sample chart data - replace with real data
  const chartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        data: [0, 150, 300, 250, 400, 350],
        color: (opacity = 1) => `rgba(76, 175, 80, ${opacity})`,
        strokeWidth: 2,
      },
    ],
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
      r: '6',
      strokeWidth: '2',
      stroke: '#4CAF50',
    },
  };

  if (loading && !performance) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <LinearGradient
        colors={['#1a1a2e', '#16213e']}
        style={styles.header}
      >
        <View style={styles.statusContainer}>
          <View style={styles.connectionStatus}>
            <Ionicons
              name={isConnected ? 'wifi' : 'wifi-outline'}
              size={20}
              color={isConnected ? '#4CAF50' : '#f44336'}
            />
            <Text style={styles.statusText}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </Text>
          </View>
          
          <Chip
            mode="outlined"
            textStyle={{ color: botStatus.running ? '#4CAF50' : '#f44336' }}
            style={{
              borderColor: botStatus.running ? '#4CAF50' : '#f44336',
            }}
          >
            {botStatus.running ? 'Bot Running' : 'Bot Stopped'}
          </Chip>
        </View>

        <View style={styles.controlButtons}>
          <Button
            mode="contained"
            onPress={handleStartBot}
            disabled={botStatus.running}
            style={[styles.button, { backgroundColor: '#4CAF50' }]}
            labelStyle={{ color: 'white' }}
          >
            Start Bot
          </Button>
          <Button
            mode="contained"
            onPress={handleStopBot}
            disabled={!botStatus.running}
            style={[styles.button, { backgroundColor: '#f44336' }]}
            labelStyle={{ color: 'white' }}
          >
            Stop Bot
          </Button>
        </View>
      </LinearGradient>

      <View style={styles.content}>
        {/* Performance Cards */}
        <View style={styles.metricsContainer}>
          <Card style={styles.metricCard}>
            <Card.Content>
              <Text style={styles.metricLabel}>Total Profit</Text>
              <Text style={styles.metricValue}>
                ${performance?.total_profit?.toFixed(2) || '0.00'}
              </Text>
            </Card.Content>
          </Card>

          <Card style={styles.metricCard}>
            <Card.Content>
              <Text style={styles.metricLabel}>Win Rate</Text>
              <Text style={styles.metricValue}>
                {(performance?.win_rate * 100)?.toFixed(1) || '0.0'}%
              </Text>
            </Card.Content>
          </Card>

          <Card style={styles.metricCard}>
            <Card.Content>
              <Text style={styles.metricLabel}>Total Trades</Text>
              <Text style={styles.metricValue}>
                {performance?.total_trades || 0}
              </Text>
            </Card.Content>
          </Card>

          <Card style={styles.metricCard}>
            <Card.Content>
              <Text style={styles.metricLabel}>Max Drawdown</Text>
              <Text style={[styles.metricValue, { color: '#f44336' }]}>
                {(performance?.max_drawdown * 100)?.toFixed(1) || '0.0'}%
              </Text>
            </Card.Content>
          </Card>
        </View>

        {/* Equity Curve Chart */}
        <Card style={styles.chartCard}>
          <Card.Content>
            <Text style={styles.chartTitle}>Equity Curve</Text>
            <LineChart
              data={chartData}
              width={screenWidth - 60}
              height={220}
              chartConfig={chartConfig}
              bezier
              style={styles.chart}
            />
          </Card.Content>
        </Card>

        {/* Recent Activity */}
        <Card style={styles.activityCard}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Recent Activity</Text>
            <View style={styles.activityItem}>
              <Ionicons name="trending-up" size={20} color="#4CAF50" />
              <Text style={styles.activityText}>
                Bot started at {new Date().toLocaleTimeString()}
              </Text>
            </View>
            <View style={styles.activityItem}>
              <Ionicons name="analytics" size={20} color="#2196F3" />
              <Text style={styles.activityText}>
                Performance updated
              </Text>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f0f23',
  },
  loadingText: {
    color: '#fff',
    marginTop: 10,
    fontSize: 16,
  },
  header: {
    padding: 20,
    paddingTop: 40,
  },
  statusContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusText: {
    color: '#fff',
    marginLeft: 8,
    fontSize: 16,
  },
  controlButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  button: {
    flex: 1,
    marginHorizontal: 10,
  },
  content: {
    padding: 20,
  },
  metricsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  metricCard: {
    width: '48%',
    marginBottom: 10,
    backgroundColor: '#1a1a2e',
  },
  metricLabel: {
    color: '#888',
    fontSize: 12,
    marginBottom: 5,
  },
  metricValue: {
    color: '#4CAF50',
    fontSize: 18,
    fontWeight: 'bold',
  },
  chartCard: {
    marginBottom: 20,
    backgroundColor: '#1a1a2e',
  },
  chartTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  activityCard: {
    backgroundColor: '#1a1a2e',
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  activityText: {
    color: '#ccc',
    marginLeft: 10,
    fontSize: 14,
  },
});

export default DashboardScreen;
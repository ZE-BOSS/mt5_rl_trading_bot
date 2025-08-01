import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  FlatList,
} from 'react-native';
import { Card, Button, Chip, ActivityIndicator } from 'react-native-paper';
import { Ionicons } from '@expo/vector-icons';
import { showMessage } from 'react-native-flash-message';

import { apiService } from '../services/api';
import { useWebSocket } from '../context/WebSocketContext';

interface Position {
  ticket: number;
  symbol: string;
  type: 'buy' | 'sell';
  volume: number;
  price_open: number;
  price_current: number;
  profit: number;
  sl: number;
  tp: number;
}

const PositionsScreen: React.FC = () => {
  const { isConnected, positions: wsPositions } = useWebSocket();
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadPositions();
  }, []);

  useEffect(() => {
    if (wsPositions && wsPositions.length > 0) {
      setPositions(wsPositions);
    }
  }, [wsPositions]);

  const loadPositions = async () => {
    try {
      setLoading(true);
      const response = await apiService.getPositions();
      setPositions(response.data.positions || []);
    } catch (error) {
      showMessage({
        message: 'Failed to load positions',
        type: 'danger',
      });
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadPositions();
    setRefreshing(false);
  };

  const getTotalProfit = () => {
    return positions.reduce((total, position) => total + position.profit, 0);
  };

  const getPositionsByType = (type: 'buy' | 'sell') => {
    return positions.filter(position => position.type === type);
  };

  const renderPosition = ({ item }: { item: Position }) => (
    <Card style={styles.positionCard}>
      <Card.Content>
        <View style={styles.positionHeader}>
          <View style={styles.symbolContainer}>
            <Text style={styles.symbolText}>{item.symbol}</Text>
            <Chip
              mode="outlined"
              textStyle={{
                color: item.type === 'buy' ? '#4CAF50' : '#f44336',
                fontSize: 12,
              }}
              style={{
                borderColor: item.type === 'buy' ? '#4CAF50' : '#f44336',
                height: 25,
              }}
            >
              {item.type.toUpperCase()}
            </Chip>
          </View>
          <Text
            style={[
              styles.profitText,
              { color: item.profit >= 0 ? '#4CAF50' : '#f44336' },
            ]}
          >
            {item.profit >= 0 ? '+' : ''}${item.profit.toFixed(2)}
          </Text>
        </View>

        <View style={styles.positionDetails}>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Volume:</Text>
            <Text style={styles.detailValue}>{item.volume}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Open Price:</Text>
            <Text style={styles.detailValue}>{item.price_open.toFixed(5)}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Current Price:</Text>
            <Text style={styles.detailValue}>{item.price_current.toFixed(5)}</Text>
          </View>
          {item.sl > 0 && (
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Stop Loss:</Text>
              <Text style={styles.detailValue}>{item.sl.toFixed(5)}</Text>
            </View>
          )}
          {item.tp > 0 && (
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Take Profit:</Text>
              <Text style={styles.detailValue}>{item.tp.toFixed(5)}</Text>
            </View>
          )}
        </View>

        <View style={styles.positionActions}>
          <Button
            mode="outlined"
            onPress={() => {
              // Implement modify position functionality
              showMessage({
                message: 'Modify position feature coming soon',
                type: 'info',
              });
            }}
            style={styles.actionButton}
            labelStyle={{ color: '#2196F3' }}
          >
            Modify
          </Button>
          <Button
            mode="contained"
            onPress={() => {
              // Implement close position functionality
              showMessage({
                message: 'Close position feature coming soon',
                type: 'info',
              });
            }}
            style={[styles.actionButton, { backgroundColor: '#f44336' }]}
            labelStyle={{ color: 'white' }}
          >
            Close
          </Button>
        </View>
      </Card.Content>
    </Card>
  );

  if (loading && positions.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4CAF50" />
        <Text style={styles.loadingText}>Loading positions...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Summary Header */}
      <Card style={styles.summaryCard}>
        <Card.Content>
          <View style={styles.summaryHeader}>
            <View style={styles.connectionStatus}>
              <Ionicons
                name={isConnected ? 'wifi' : 'wifi-outline'}
                size={20}
                color={isConnected ? '#4CAF50' : '#f44336'}
              />
              <Text style={styles.connectionText}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </Text>
            </View>
            <Button
              mode="outlined"
              onPress={loadPositions}
              style={styles.refreshButton}
              labelStyle={{ color: '#4CAF50' }}
            >
              Refresh
            </Button>
          </View>

          <View style={styles.summaryStats}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Total Positions</Text>
              <Text style={styles.statValue}>{positions.length}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Buy Positions</Text>
              <Text style={styles.statValue}>{getPositionsByType('buy').length}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Sell Positions</Text>
              <Text style={styles.statValue}>{getPositionsByType('sell').length}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>Total P&L</Text>
              <Text
                style={[
                  styles.statValue,
                  { color: getTotalProfit() >= 0 ? '#4CAF50' : '#f44336' },
                ]}
              >
                {getTotalProfit() >= 0 ? '+' : ''}${getTotalProfit().toFixed(2)}
              </Text>
            </View>
          </View>
        </Card.Content>
      </Card>

      {/* Positions List */}
      {positions.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Ionicons name="list-outline" size={64} color="#666" />
          <Text style={styles.emptyText}>No open positions</Text>
          <Text style={styles.emptySubtext}>
            Your open positions will appear here
          </Text>
        </View>
      ) : (
        <FlatList
          data={positions}
          renderItem={renderPosition}
          keyExtractor={(item) => item.ticket.toString()}
          style={styles.positionsList}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
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
  summaryCard: {
    margin: 20,
    backgroundColor: '#1a1a2e',
  },
  summaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  connectionText: {
    color: '#fff',
    marginLeft: 8,
    fontSize: 16,
  },
  refreshButton: {
    borderColor: '#4CAF50',
  },
  summaryStats: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statItem: {
    width: '48%',
    marginBottom: 10,
  },
  statLabel: {
    color: '#888',
    fontSize: 12,
    marginBottom: 5,
  },
  statValue: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  positionsList: {
    flex: 1,
    paddingHorizontal: 20,
  },
  positionCard: {
    marginBottom: 15,
    backgroundColor: '#1a1a2e',
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  symbolContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  symbolText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginRight: 10,
  },
  profitText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  positionDetails: {
    marginBottom: 15,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 5,
  },
  detailLabel: {
    color: '#888',
    fontSize: 14,
  },
  detailValue: {
    color: '#ccc',
    fontSize: 14,
  },
  positionActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    flex: 1,
    marginHorizontal: 5,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginTop: 20,
    textAlign: 'center',
  },
  emptySubtext: {
    color: '#888',
    fontSize: 16,
    marginTop: 10,
    textAlign: 'center',
  },
});

export default PositionsScreen;
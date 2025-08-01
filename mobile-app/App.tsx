import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Provider as PaperProvider } from 'react-native-paper';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import FlashMessage from 'react-native-flash-message';

import DashboardScreen from './src/screens/DashboardScreen';
import TradingScreen from './src/screens/TradingScreen';
import PositionsScreen from './src/screens/PositionsScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import BacktestScreen from './src/screens/BacktestScreen';

import { WebSocketProvider } from './src/context/WebSocketContext';
import { theme } from './src/theme/theme';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <PaperProvider theme={theme}>
      <WebSocketProvider>
        <NavigationContainer>
          <StatusBar style="light" backgroundColor="#1a1a2e" />
          <Tab.Navigator
            screenOptions={({ route }) => ({
              tabBarIcon: ({ focused, color, size }) => {
                let iconName: keyof typeof Ionicons.glyphMap;

                if (route.name === 'Dashboard') {
                  iconName = focused ? 'analytics' : 'analytics-outline';
                } else if (route.name === 'Trading') {
                  iconName = focused ? 'trending-up' : 'trending-up-outline';
                } else if (route.name === 'Positions') {
                  iconName = focused ? 'list' : 'list-outline';
                } else if (route.name === 'Backtest') {
                  iconName = focused ? 'bar-chart' : 'bar-chart-outline';
                } else if (route.name === 'Settings') {
                  iconName = focused ? 'settings' : 'settings-outline';
                } else {
                  iconName = 'help-outline';
                }

                return <Ionicons name={iconName} size={size} color={color} />;
              },
              tabBarActiveTintColor: '#4CAF50',
              tabBarInactiveTintColor: '#888',
              tabBarStyle: {
                backgroundColor: '#1a1a2e',
                borderTopColor: '#333',
                height: 60,
                paddingBottom: 8,
                paddingTop: 8,
              },
              headerStyle: {
                backgroundColor: '#1a1a2e',
              },
              headerTintColor: '#fff',
              headerTitleStyle: {
                fontWeight: 'bold',
              },
            })}
          >
            <Tab.Screen name="Dashboard" component={DashboardScreen} />
            <Tab.Screen name="Trading" component={TradingScreen} />
            <Tab.Screen name="Positions" component={PositionsScreen} />
            <Tab.Screen name="Backtest" component={BacktestScreen} />
            <Tab.Screen name="Settings" component={SettingsScreen} />
          </Tab.Navigator>
          <FlashMessage position="top" />
        </NavigationContainer>
      </WebSocketProvider>
    </PaperProvider>
  );
}
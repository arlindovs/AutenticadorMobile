import * as React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import ConfigScreen from './screens/ConfigScreen';
import LoginScreen from './screens/LoginScreen';
// import TotpScreen from './screens/TotpScreen';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
      <NavigationContainer>
        <Stack.Navigator initialRouteName="Config" screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Config" component={ConfigScreen} />
          <Stack.Screen name="Login" component={LoginScreen} />
          {/*<Stack.Screen name="Totp" component={TotpScreen} />*/}
        </Stack.Navigator>
      </NavigationContainer>
  );
}

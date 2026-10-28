import React from 'react';
import { View } from 'react-native';

import { useTheme } from '@/hooks/use-theme';

export function ThemedView({ style, lightColor, darkColor, type, ...otherProps }) {
  const theme = useTheme();

  return <View style={[{ backgroundColor: theme[type || 'background'] }, style]} {...otherProps} />;
}

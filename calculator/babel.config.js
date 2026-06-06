module.exports = {
  presets: [
    [
      'babel-preset-taro',
      {
        framework: 'react',
        ts: true,
        useBuiltIns: 'usage',
        targets: { ios: '10', android: '7' },
      },
    ],
  ],
};

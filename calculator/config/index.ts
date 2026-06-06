import { defineConfig } from '@tarojs/cli';
import type { IProjectConfig } from '@tarojs/taro/types/compile/config/project';

export default defineConfig(async (merge, { command, mode }) => {
  const base: Partial<IProjectConfig> = {
    projectName: 'calculator',
    date: '2026-6-6',
    designWidth: 750,
    deviceRatio: { 640: 2.34 / 2, 750: 1, 375: 2 / 1, 414: 1.9 / 2 },
    sourceRoot: 'src',
    outputRoot: 'dist',
    plugins: ['@tarojs/plugin-framework-react'],
    framework: 'react',
    compiler: 'webpack5',
    cache: { enable: true },
    sass: { resource: [] },
    defineConstants: {},
    copy: { patterns: [], options: {} },
  };

  if (mode === 'development') {
    return merge({}, base, {
      h5: {
        devServer: { port: 10086, host: '0.0.0.0', https: false },
        publicPath: '/',
      },
    } as Partial<IProjectConfig>);
  }

  return merge({}, base, {
    h5: {
      publicPath: './',
      staticDirectory: 'static',
      output: {
        filename: 'js/[name].[contenthash:8].js',
        chunkFilename: 'js/[name].[contenthash:8].js',
      },
      miniCssExtractPluginOption: {
        ignoreOrder: true,
        filename: 'css/[name].[contenthash:8].css',
      },
      postcss: {
        autoprefixer: { enable: true },
      },
    },
  } as Partial<IProjectConfig>);
});

// Expo configures Metro for the pnpm monorepo itself; NativeWind adds Tailwind.
const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

module.exports = withNativeWind(getDefaultConfig(__dirname), {
  input: "./src/global.css",
});

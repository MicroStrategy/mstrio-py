module.exports = {
  env: {
    browser: true,
    worker: true,
    amd: true,
    webextensions: true,
  },
  extends: [
    'airbnb-base',
  ],
  parserOptions: {
    impliedStrict: true,
  },
  parser: "babel-eslint",
  rules: {
    "import/no-amd": "off",
    "max-len": ["warn", 250],
    "object-curly-newline": ["warn", { ObjectPattern: { multiline: true } }],
    "no-param-reassign": ["error", { props: false }],
    "no-unused-expressions": ["error", { allowShortCircuit: true }],
    "spaced-comment": "warn",
    "func-names": "off",
    "no-console": "off",
  },
};

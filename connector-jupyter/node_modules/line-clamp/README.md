# line-clamp [![npm Version](https://badgen.net/npm/v/line-clamp)](https://www.npmjs.org/package/line-clamp) [![Build Status](https://badgen.net/travis/yuanqing/line-clamp?label=build)](https://travis-ci.org/yuanqing/line-clamp) [![Bundle Size](https://badgen.net/bundlephobia/minzip/line-clamp)](https://bundlephobia.com/result?p=line-clamp)

> Line clamp a DOM element in vanilla JavaScript

- Truncates in pure JavaScript; does *not* rely on [`-webkit-line-clamp`](https://css-tricks.com/line-clampin/)
- Works even if the given element contains nested DOM nodes
- Supports appending a custom string instead of an ellipsis (`…`)

## Usage

> [**Editable demo (CodePen)**](https://codepen.io/lyuanqing/pen/VQQVry)

HTML:

```html
<div class="line-clamp">
  Lorem ipsum dolor sit amet, <strong>consectetur adipiscing</strong> elit.
</div>
```

CSS:

```css
.line-clamp {
  width: 100px;
  line-height: 20px;
}
```

JavaScript:

```js
const element = document.querySelector('.line-clamp')
lineClamp(element, 3)
```

Boom:

```html
<div class="line-clamp" style="overflow: hidden; overflow-wrap: break-word; word-wrap: break-word;">
  Lorem ipsum dolor sit amet, <strong>consectetur…</strong>
</div>
```

### Limitations

- The element is assumed to have a pixel line-height, obtained via [`window.getComputedStyle`](https://developer.mozilla.org/en-US/docs/Web/API/Window/getComputedStyle).

## API

```js
const lineClamp = require('line-clamp')
```

### lineClamp(element, lineCount [, options])

Returns `true` if text was truncated, else returns `false`.

`options` is an optional configuration object.

- Set `options.ellipsis` to change the string to be appended to the truncated text. Defaults to `…`.

See [Usage](#usage).

## Installation

```sh
$ yarn add line-clamp
```

## Prior art

- [Clamp.js](https://github.com/josephschmitt/Clamp.js)
- [FTEllipsis](https://github.com/ftlabs/ftellipsis)
- [Shave](https://github.com/dollarshaveclub/shave)

## License

[MIT](LICENSE.md)

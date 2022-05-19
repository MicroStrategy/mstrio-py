define(['./globals'], ({ GLOBAL_CONSTANTS }) => class Utilities {
  static changeSize(mode, element) {
    switch (mode) {
      case 'authentication':
      case 'loading':
        Utilities.applyStyles(element, {
          maxWidth: '538px',
          maxHeight: '661px',
          height: '90%',
        });
        break;
      case 'app-selection':
      case 'export-update-policy-selection':
        Utilities.applyStyles(element, {
          maxWidth: '560px',
          maxHeight: '700px',
          height: '90%',
        });
        break;
      default:
        Utilities.applyStyles(element, {
          maxWidth: '1350px',
          maxHeight: '850px',
          width: '80%',
          height: '80%',
        });
        break;
    }
  }


  static createElement(tag, attributes = {}, ..._args) {
    /* function to replace jQuery when possible
     * {param} tag: STRING - tag name to create
     * {param} attributes: OBJECT (opt) - key: name of attribute, value: value of attribute
     * EITHER
     *    {param} parent: DOMElement (opt): DOM elem which is a parent (optional if beforeElement is provided)
     *    {param} beforeElement: DOMElement (opt): DOM elem before which new one should be
     *                                             (optional if parent is provided)
     * OR
     *    {param} children: Array of DOM Elements (opt): list of DOM Elements which will be appended to created element
     * OR
     *    {param} parent: DOMElement (opt): DOM elem which is a parent (optional if beforeElement is provided)
     *    {param} children: Array of DOM Elements (opt): list of DOM Elements which will be appended to created element
     *    {param} beforeElement: DOMElement (opt): DOM elem before which new one should be
     *                                             (optional if parent is provided)
    */
    const args = {};
    if (_args[0] instanceof Array) [args.children] = _args;
    else if (_args[1] && _args[1] instanceof Array) [args.parent, args.children, args.beforeElement] = _args;
    else [args.parent, args.beforeElement] = _args;

    const element = document.createElement(tag);
    Object.keys(attributes).forEach((key) => {
      element.setAttribute(key, attributes[key]);
    });

    args.parent && args.parent.appendChild(element);
    args.beforeElement && args.beforeElement.parentNode.insertBefore(element, args.beforeElement);
    args.children && args.children.forEach((child) => {
      element.appendChild(child);
    });

    return element;
  }


  static applyCustomStyleFile(filePath, elementTo = window.document) {
    const verifier = Utilities.lastElement(filePath.split('.'));
    if (verifier !== 'css') {
      throw new Error(
        'Utilities.applyCustomStyleFile() error: unrecognized type of styles file provided (only ".css" is applicable)',
      );
    }
    const { ORIGIN, EXTENSION_MAIN_FOLDER } = GLOBAL_CONSTANTS;
    try {
      const href = `${ORIGIN}${EXTENSION_MAIN_FOLDER}/${
        Utilities.lastElement(filePath.split('/'))
      }`;
      const link = window.document.createElement('link');
      link.setAttribute('href', href);
      link.setAttribute('rel', 'stylesheet');
      link.setAttribute('type', 'text/css');
      elementTo.head.appendChild(link);
    } catch (err) {
      console.error(err);
      throw new Error(
        'Utilities.applyCustomStyleFile() error: applying custom styles to Jupyter Notebook was unsuccessful',
      );
    }
  }


  static XOR(_a, _b) {
    const a = !!_a;
    const b = !!_b;
    return (a ? !b : b);
  }


  // eslint-disable-next-line consistent-return
  static lastElement(iterableObject, _indexOffset = 0) {
    try {
      if (!iterableObject.length) return undefined;
      const indexOffset = Math.abs(_indexOffset) > iterableObject.length - 1
        ? 0
        : Math.abs(_indexOffset);
      return iterableObject[iterableObject.length - 1 - indexOffset];
    } catch (err) {
      console.error(err);
    }
  }


  static flagImportExport(state) {
    window.backendManager && window.backendManager.toggleImportOrExportInProgress(state);
    localStorage.setItem('mstr-import-export', state.toString());
  }


  static properCase(text) {
    return text.replace(
      /\w\S*/g,
      (txt) => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase(),
    );
  }


  static formatDateToUS(date) {
    const calcHours = (hoursNum) => (
      hoursNum === 12 // avoids displaying 0 on noon
        ? 12
        : hoursNum % 12
    );

    const details = {
      day: date.getDate().toString().padStart(2, '0'),
      month: (date.getMonth() + 1).toString().padStart(2, '0'), // 0-indexed
      year: date.getFullYear(),

      hours: calcHours(date.getHours()).toString().padStart(2, '0'),
      minutes: date.getMinutes().toString().padStart(2, '0'),
      seconds: date.getSeconds().toString().padStart(2, '0'),
      suffix: date.getHours() >= 12 ? 'PM' : 'AM',
    };

    return `${
      details.month
    }/${
      details.day
    }/${
      details.year
    } ${
      details.hours
    }:${
      details.minutes
    }:${
      details.seconds
    } ${
      details.suffix
    }`;
  }


  // utilities sub-engine functions (used in proper functionalities of Utilities class)
  static applyStyles(element, styles) {
    Object.keys(styles).forEach((key) => {
      element.style[key] = styles[key];
    });
  }

  static removeElementsByClass(className) {
    [...document.getElementsByClassName(className)].forEach(
      (element) => element.remove(),
    );
  }
});

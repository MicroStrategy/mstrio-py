define([], () => class Utilities {
  static changeSize = (mode, element) => {
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
        Utilities.applyStyles(element, {
          maxWidth: '538px',
          maxHeight: '706px',
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


  static applyCustomStyleFile = (filePath, elementTo = window.document) => {
    const verifier = Utilities.lastElement(filePath.split('.'));
    if (verifier !== 'css') {
      throw new Error('Utilities.applyCustomStyleFile() error: unrecognized type of styles file provided (only ".css" is applicable)');
    }
    try {
      const href = `${Utilities.consts.ORIGIN}${Utilities.consts.EXTENSION_MAIN_FOLDER}/${Utilities.lastElement(filePath.split('/'))}`;
      const link = window.document.createElement('link');
      link.setAttribute('href', href);
      link.setAttribute('rel', 'stylesheet');
      link.setAttribute('type', 'text/css');
      elementTo.head.appendChild(link);
    } catch (err) {
      console.error(err);
      throw new Error('Utilities.applyCustomStyleFile() error: applying custom styles to Jupyter Notebook was unsuccessful');
    }
  }


  static messageTypes = {
    applyDataframeChangesSteps: 'apply-dataframe-changes-steps',
    connectionDataUpdate: 'connection-data-update',
    createExportCell: 'create-export-cell',
    createImportCell: 'create-import-cell',
    createUpdateCell: 'create-update-cell',
    gatherDataframeContent: 'gather-dataframe-content',
    initializeConnectorUi: 'initialize-connector-ui',
    refreshExportDetails: 'refresh-export-details',
    uiScreenChange: 'ui-screen-change',
    updateEnvironmentsList: 'update-environments-list',
    updateProjectsList: 'update-projects-list',
  }


  static consts = {
    get ORIGIN() { return window.location.origin; },
    get EXTENSION_MAIN_FOLDER() { return '/nbextensions/mstr_jupyter'; },
    get EXTENSION_PATHNAME() { return `${this.EXTENSION_MAIN_FOLDER}/mstr-connector/build/index.html`; },
    get CONNECTOR_ADDRESS() { return `${this.ORIGIN}${this.EXTENSION_PATHNAME}`; },
    get MSTR_ENV_VARIABLE_NAME() { return 'mstrio_env'; },
  }


  // eslint-disable-next-line consistent-return
  static lastElement = (iterableObject, _indexOffset = 0) => {
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


  // utilities sub-engine functions (used in proper functionalities of Utilities class)
  static applyStyles = (element, styles) => {
    Object.keys(styles).forEach((key) => {
      element.style[key] = styles[key];
    });
  }
});


// ------ LEFT FOR EASE OF REFERENCE FOR FURTHER DEVELOPMENT --------
// window.backendManager.toggleImportOrExportInProgress(true / false);

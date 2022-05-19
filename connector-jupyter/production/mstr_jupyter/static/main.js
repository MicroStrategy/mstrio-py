define(['./jupyter-cell', './jupyter-kernel', './python-code', './utilities', './globals', // custom files
  'jquery', 'base/js/namespace', 'base/js/dialog', 'base/js/events'], // general or Jupyter related
(
  JupyterCell, JupyterKernel, PythonCode, Utilities, Globals,
  $, Jupyter, Dialog, Events,
) => { // NOSONAR (Too many params: need to stay as this is the way to implement `define()`)
  const {
    GLOBAL_CONSTANTS: {
      MSTR_ENV_VARIABLE_NAME,
      EXTENSION_PATHNAME, EXTENSION_MAIN_FOLDER,
      CONNECTOR_ADDRESS, ORIGIN,
    },
    CELL_METADATA, MESSAGE_TYPES, RESPONSE_TYPES,
  } = Globals;

  // initial consts
  const INITIAL_ENGINE = new JupyterKernel(
    Jupyter.notebook.kernel,
    { customEnvironment: MSTR_ENV_VARIABLE_NAME },
  );

  window.jupyterKernelUniqueID = 0;

  let uiIframeModal;
  let currentMode;
  let authenticationDetails;

  // object created for support "copy to clipboard" functionality (ver. 2 for compatibility)
  Utilities.createElement('textarea', { id: 'mstr-copy-to-clipboard-object' }, document.body);

  // === Unique One-Time Declarations only onExtensionLoad ===
  const applyCustomEnvironmentEngine = () => ( // function applying custom environment engine to the Jupyter
    INITIAL_ENGINE
      .setCustomEnvironmentEngine()
      .verifyCustomEnvironment()
  );

  window.debugMSTR = {
    JupyterCell,
    JupyterKernel,
    PythonCode,
    Utilities,
    initialEngine: INITIAL_ENGINE,
    applyCustomEnvironmentEngine,
    uiIframeModal: () => uiIframeModal,
  };

  // [CUSTOM JUPYTER EVENTS Listeners]
  Events.on('select.Cell', (_, { cell }) => { // onCellSelect lock possibility to change type of MSTRCell
    const cellTypeSelector = document.querySelector('#cell_type');
    const cellTypeMenu = document.querySelector('#change_cell_type');
    if (cell.metadata[CELL_METADATA.IS_MSTR]) {
      cellTypeSelector.setAttribute('disabled', 'disabled');
      cellTypeMenu.classList.add('force-disabled');
    } else {
      cellTypeSelector.setAttribute('disabled', false);
      cellTypeMenu.classList.remove('force-disabled');
    }
  });

  Events.on('execute.MSTRCell', (_, { cell }) => {
    cell.buttonsToLockOnRun.forEach((button) => button.disable());
  });

  Events.on('finished_execute.MSTRCell', (_, { cell }) => {
    cell.buttonsToLockOnRun.forEach((button) => button.enable());
    cell.focus(); // return focus to cell for keyboard manager custom options
  });

  Events.on('create.Cell', (_, { cell, index }) => { // fired when cell created by default Jup ways
    setTimeout(() => {
      /** Timeout required due to very strange implementation of metadata saving in Jup.
       * It is a sync approach simulating async structure. (Too complex to describe here)
       * There is nothing to await within this event, hence workaround required.
       * source: Jup GitHub: /notebook/static/notebook/js/notebook.js#L1331
       */
      const { metadata } = cell;
      if (metadata[CELL_METADATA.IS_MSTR]) {
        // created custom cell by non-custom approach, hence reapply custom cell engine
        // possible reasons: cell copy+paste, cell cut+paste, multi-cell-selection manipulation, etc.
        new JupyterCell(Jupyter.notebook, metadata)
          .recreateCell(index);
        Jupyter.notebook.select(index);
      }
    }, 50);
  });

  Events.on('kernel_idle.Kernel', () => { Utilities.flagImportExport(false); });
  // ===

  const restructureTypesToMatchRStudio = (_result) => {
    // clearing structure to copy RStudio output architecture
    const result = { ..._result };
    result.attributes = result.attributes.map((item) => ({
      ...item,
      name: [item.name],
    }));
    result.metrics = result.metrics.map((item) => ({
      ...item,
      name: [item.name],
    }));
    result.tables[0].columnHeaders = result.tables[0].columnHeaders.map((item) => ({
      ...item,
      name: [item.name],
    }));
    return result;
  };

  const listenerForCustomCellResponses = (event) => { // listener for Custom Cell Data Requests responses
    const { data: { responseType, responseDetails } } = event;
    const { backendManager } = window;

    switch (responseType) {
      // save new data
      case RESPONSE_TYPES.UPDATE_IMPORT: {
        uiIframeModal.modal('hide');

        const { body, instanceId, identityToken, cellIndex } = responseDetails;
        const cell = Jupyter.notebook.get_cell(cellIndex);
        const { otherDetails, dataframeDetails } = cell.metadata[CELL_METADATA.DATA];
        authenticationDetails = { ...authenticationDetails, identityToken };
        const freshDataframeDetails = {
          ...dataframeDetails,
          body,
          instanceId,
        };
        const existingMetadata = { ...cell.metadata };
        existingMetadata[CELL_METADATA.DATA].dataframeDetails = freshDataframeDetails;

        new JupyterCell(Jupyter.notebook, authenticationDetails, freshDataframeDetails, otherDetails, existingMetadata)
          .removePrevious(cellIndex)
          .forImport(cellIndex);
        break;
      }
      case RESPONSE_TYPES.UPDATE_EXPORT: {
        uiIframeModal.modal('hide');

        const { dataframeDetails, otherDetails, identityToken, cellIndex } = responseDetails;
        const cell = Jupyter.notebook.get_cell(cellIndex);
        const {
          otherDetails: otherDetailsOld,
          dataframeDetails: dataframeDetailsOld,
        } = cell.metadata[CELL_METADATA.DATA];
        const existingMetadata = { ...cell.metadata };
        existingMetadata[CELL_METADATA.DATA].dataframeDetails = {
          ...dataframeDetailsOld,
          ...dataframeDetails,
        };
        existingMetadata[CELL_METADATA.DATA].otherDetails = {
          ...otherDetailsOld,
          ...otherDetails,
        };

        authenticationDetails = { ...authenticationDetails, identityToken };

        new JupyterCell(
          Jupyter.notebook,
          authenticationDetails,
          existingMetadata[CELL_METADATA.DATA].dataframeDetails,
          existingMetadata[CELL_METADATA.DATA].otherDetails,
          existingMetadata,
        )
          .removePrevious(cellIndex)
          .forExport(cellIndex);
        break;
      }
      case RESPONSE_TYPES.UPDATE_UPDATE: {
        uiIframeModal.modal('hide');

        const { otherDetails, identityToken, cellIndex } = responseDetails;
        const cell = Jupyter.notebook.get_cell(cellIndex);
        const {
          dataframeDetails,
          otherDetails: otherDetailsOld,
        } = cell.metadata[CELL_METADATA.DATA];
        const existingMetadata = { ...cell.metadata };
        existingMetadata[CELL_METADATA.DATA].otherDetails = {
          ...otherDetailsOld,
          ...otherDetails,
        };
        authenticationDetails = { ...authenticationDetails, identityToken };

        new JupyterCell(
          Jupyter.notebook,
          authenticationDetails,
          dataframeDetails,
          existingMetadata[CELL_METADATA.DATA].otherDetails,
          existingMetadata,
        )
          .removePrevious(cellIndex)
          .forUpdate(cellIndex);
        break;
      }

      // prepare for edition
      case RESPONSE_TYPES.PREPARE_EXPORT:
      case RESPONSE_TYPES.PREPARE_UPDATE: {
        const { requiredDataframes } = responseDetails;

        INITIAL_ENGINE
          .resetCustomEnvironment()
          .then(() => {
            new JupyterKernel(Jupyter.notebook.kernel, { customEnvironment: MSTR_ENV_VARIABLE_NAME })
              .code(PythonCode.code().forGettingDataframesNames)
              .execute()
              .then((self) => {
                const dataframes = self.getResult().map(({ name }) => name);
                if (requiredDataframes.every((df) => dataframes.includes(df))) {
                  // if all required data is available in kernel:
                  self
                    .then(() => {
                      // get details of all dataframes:
                      const finalDataframes = {};
                      const detailsGatherers = requiredDataframes
                        .map((df) => new JupyterKernel(Jupyter.notebook.kernel, { name: df })
                          .code(PythonCode.code().forGettingDataframeData)
                          .execute()
                          .then((that) => {
                            finalDataframes[df] = {
                              originalName: df,
                              content: that.getResult(),
                            };
                            that
                              .code(PythonCode.code().forModelingGatheredData)
                              .execute()
                              .then((selfFinal) => {
                                const result = restructureTypesToMatchRStudio(selfFinal.getResult());
                                finalDataframes[df].types = result;
                                selfFinal.done();
                              });
                          }));
                      JupyterKernel.awaitAll(detailsGatherers, true)
                        .then(() => {
                          backendManager.applyDataframes(JSON.stringify(finalDataframes));
                        });
                    });
                } else {
                  // some dataframes are missing:
                  backendManager.showLackingDFEditError(
                    requiredDataframes,
                    () => uiIframeModal.modal('hide'),
                  );
                }
              });
          });
        break;
      }

      default: break;
    }
  };

  const listenerForUiFunctionalities = (event) => { // main mstr listener for connection with UI functionalities
    const { backendManager } = window;

    const {
      data: {
        messageType, authInfo, dataframeDetails, otherDetails = {}, middlewareDetails,
        identityToken,
      },
    } = event;
    const {
      initializeConnectorUi, updateEnvironmentsList, updateProjectsList, uiScreenChange,
      connectionDataUpdate, gatherDataframeContent, refreshExportDetails, closeUI, consoleMSG,
      createExportCell, createUpdateCell, createImportCell, applyDataframeChangesSteps,
    } = MESSAGE_TYPES;

    otherDetails.customEnvironment = MSTR_ENV_VARIABLE_NAME;

    authenticationDetails = { ...authenticationDetails, identityToken };

    switch (messageType) {
      // debug
      case consoleMSG: {
        const { message } = event.data;
        // eslint-disable-next-line no-console
        console.log(message);
        window.DEBUG_MESSAGE = message;
        break;
      }

      // preparation and middleware update cases
      case closeUI: {
        uiIframeModal.modal('hide');
        break;
      }
      case initializeConnectorUi: {
        const iframeDocument = document.querySelector('iframe#mstr-iframe').contentWindow.document;
        Utilities.applyCustomStyleFile('ui-iframe.css', iframeDocument);

        const environments = localStorage.getItem('mstr-environments');
        const projects = localStorage.getItem('mstr-projects');

        environments && backendManager.addEnvToSuggestions(environments);
        projects && backendManager.addRecentProjects(projects);

        const { envName = authenticationDetails.url } = (authenticationDetails || {});
        // no envName provided => use url
        const selectedProjectsList = projects && envName
          ? JSON.parse(projects)[envName] || []
          : [];

        if (currentMode !== 'authentication' && selectedProjectsList.length && authenticationDetails) {
          backendManager.automaticLogin(
            authenticationDetails, authenticationDetails.authToken, currentMode, selectedProjectsList,
          );
        } else backendManager.showAuthenticationPage();

        new JupyterKernel(Jupyter.notebook.kernel)
          .code(PythonCode.code().forGettingPackageVersionNumber)
          .expectString()
          .execute()
          .then((self) => {
            backendManager.updatePackageVersionNumber(self.getResult());
          });

        new JupyterKernel(Jupyter.notebook.kernel)
          .code(PythonCode.code().forGettingKernelInfo)
          .execute()
          .then((self) => {
            backendManager.updateBackendParameters(JSON.stringify(self.getResult()));
          });

        new JupyterKernel(Jupyter.notebook.kernel)
          .code(PythonCode.code().forGettingDataframesNames)
          .execute()
          .then((self) => {
            backendManager.updateDataFramesList(JSON.stringify(self.getResult()));
          });

        break;
      }
      case uiScreenChange: {
        const { mode } = middlewareDetails;
        const uiIframe = document.querySelector('.modal-dialog');

        currentMode = mode;
        Utilities.changeSize(mode, uiIframe);
        break;
      }

      // code applied to Jupyter Cells cases
      case createExportCell: {
        uiIframeModal.modal('hide');
        new JupyterCell(Jupyter.notebook, authenticationDetails, dataframeDetails, otherDetails).forExport();
        break;
      }
      case createImportCell: {
        uiIframeModal.modal('hide');
        new JupyterCell(Jupyter.notebook, authenticationDetails, dataframeDetails, otherDetails).forImport();
        break;
      }
      case createUpdateCell: {
        uiIframeModal.modal('hide');
        new JupyterCell(Jupyter.notebook, authenticationDetails, dataframeDetails, otherDetails).forUpdate();
        break;
      }

      // application of middleware changes / Jupyter kernel changes cases
      case applyDataframeChangesSteps: {
        const { steps, selectedDataframes } = otherDetails;

        new JupyterKernel(Jupyter.notebook.kernel, { customEnvironment: MSTR_ENV_VARIABLE_NAME })
          .resetCustomEnvironment()
          .then((self) => {
            self.applySameOnEachElement(steps, (item, that) => {
              that
                .code(PythonCode.code().forApplyingStep, item)
                .shell()
                .execute();
            })
              .then(() => {
                const allColumnsSelections = selectedDataframes.map(({ dfName, selectedObjects }) => (
                  new JupyterKernel(Jupyter.notebook.kernel, { name: dfName, selectedObjects }, otherDetails)
                    .code(PythonCode.code().forDataframeColumnsSelection)
                    .shell()
                    .execute()
                ));
                JupyterKernel.awaitAll(allColumnsSelections).then(() => {
                  backendManager.finishDataModeling(true);
                });
              });
          });
        break;
      }

      case connectionDataUpdate: {
        authenticationDetails = authInfo;
        break;
      }

      case updateEnvironmentsList: {
        const { environments } = middlewareDetails;

        backendManager.addEnvToSuggestions(environments);
        localStorage.setItem('mstr-environments', environments);
        break;
      }
      case updateProjectsList: {
        const { projects } = middlewareDetails;

        backendManager.addRecentProjects(projects);
        localStorage.setItem('mstr-projects', projects);
        break;
      }

      // gathering data for UI cases
      case gatherDataframeContent: {
        const finalOutput = {
          originalName: dataframeDetails.originalName,
        };

        new JupyterKernel(Jupyter.notebook.kernel, dataframeDetails)
          .code(PythonCode.code().forGettingDataframeData)
          .execute()
          .then((self) => {
            finalOutput.content = self.getResult();
            self
              .code(PythonCode.code().forModelingGatheredData)
              .execute()
              .then((selfFinal) => {
                const result = restructureTypesToMatchRStudio(selfFinal.getResult());
                finalOutput.types = result;
                backendManager.updateDataFrameContent(finalOutput, dataframeDetails.name);
              });
          });
        break;
      }
      case refreshExportDetails: {
        const notebookName = document.querySelector('#notebook_name').innerText;
        backendManager.setBackendEnvName(notebookName);

        new JupyterKernel(Jupyter.notebook.kernel)
          .code(PythonCode.code().forGettingDataframesNames)
          .execute()
          .then((self) => {
            backendManager.updateDataFramesList(JSON.stringify(self.getResult()));
          });
        break;
      }

      default: break;
    }
  };

  const messageListener = (event) => { // engine to implement the listeners
    window.backendManager = document.getElementById('mstr-iframe').contentWindow.backendManager;

    // security measures:
    try {
      const { data: { messageType, responseType } } = event;

      const isFromMstrConnector = event.origin === window.top.origin
        && event.source.document.location.pathname === EXTENSION_PATHNAME;

      if (!isFromMstrConnector) {
        return;
      }

      const hasCorrectStructure = !!messageType || !!responseType;
      console.assert(hasCorrectStructure, 'Incorrect event structure:', event);
      if (!hasCorrectStructure) {
        throw new Error('Incorrect window.postMessage() event structure');
      }

      messageType && listenerForUiFunctionalities(event);
      responseType && listenerForCustomCellResponses(event);
    } catch (error) {
      console.error('Error with window.onMessage event: ', error);
      window.backendManager.displayErrorMessage('JupConnectionError', error.message);
    }
    // ---
  };

  applyCustomEnvironmentEngine();
  Utilities.applyCustomStyleFile('global-override.css');
  window.addEventListener('message', messageListener);

  const buildMstr = () => { // main function applying connection to UI
    const { createElement, removeElementsByClass } = Utilities;
    removeElementsByClass('modal cmd-palette'); // remove element that causes css error

    return $(
      createElement('div', { // container
        id: 'mstr-container',
      }, [
        createElement('iframe', { // child: iframe
          src: `${CONNECTOR_ADDRESS}?loading=true`,
          id: 'mstr-iframe',
        }),
      ]),
    );
  };

  const showMstrModal = () => { // function for displaying UI
    uiIframeModal = Dialog
      .modal({
        show: false,
        notebook: Jupyter.notebook,
        keyboard_manager: Jupyter.notebook.keyboard_manager,
        body: buildMstr(),
      })
      .attr('id', 'mstr-modal');

    const backendManagerEstablished = () => !!window.backendManager;

    return new Promise((resolve, reject) => {
      uiIframeModal
        .on('shown.bs.modal', function focusIframe() {
          $(this)
            .find('iframe#mstr-iframe')
            .focus();

          let timeout = 0;
          const interval = setInterval(() => {
            if (backendManagerEstablished()) {
              clearInterval(interval);
              resolve();
            }
            timeout += 1;
            if (timeout > 100) reject();
          }, 100);
        })
        .modal('show');
    });
  };

  const initialize = () => { // MSTRIO extension initialization function
    window.showMstrModal = showMstrModal;

    Jupyter.toolbar.add_buttons_group([
      Jupyter.keyboard_manager.actions.register({
        help: 'Connect to MicroStrategy',
        icon: ' ',
        handler: showMstrModal,
      },
      'connect-to-microstrategy',
      'mstr_it'),
    ]);

    $("[title='Connect to MicroStrategy']")
      .append(
        `<img
          src="${ORIGIN}${EXTENSION_MAIN_FOLDER}/mstr.ico"
          id="mstr-ico"
        >`,
      )
      .bind('keydown', function bindSpaceA11y(event) {
        if (event.key === ' ') {
          event.preventDefault();
          $(this).click();
        }
      });
  };

  const loadMstrExtensionToJupyter = () => ( // object required by Jupyter to load extension, as per documentation
    Jupyter.notebook.config.loaded.then(() => {
      initialize();
    })
  );

  /* As Jupyter Engine does not allow custom cell types,
   * after reopening saved ipynb the styling of custom cells need to be reapplied.
   * This is done below:
   */
  Jupyter.notebook.get_cells() // return array of cells not as DOM (but as code metadata)
    .forEach((cell, index) => {
      const { metadata } = cell;
      const isMstrCell = !!metadata[CELL_METADATA.IS_MSTR];
      cell.unselect();
      if (!isMstrCell) return;
      new JupyterCell(Jupyter.notebook, metadata)
        .recreateCell(index); // apply new
    });
  Jupyter.notebook.get_cell(0).select(); // after reapplication, select only first
  // -----

  return {
    load_jupyter_extension: loadMstrExtensionToJupyter,
    load_ipython_extension: loadMstrExtensionToJupyter,
  };
});

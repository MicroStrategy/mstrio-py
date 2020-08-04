define(['./jupyter-cells', './jupyter-kernel', './python-code', './utilities', // custom files
  'jquery', 'base/js/namespace', 'base/js/dialog'], // general or Jupyter related
(
  JupyterCell, JupyterKernel, PythonCode, Utilities,
  $, Jupyter, Dialog,
) => {
  // initial consts
  const GLOBAL_CONSTANTS = Utilities.consts;
  const INITIAL_ENGINE = new JupyterKernel(Jupyter.notebook.kernel, { customEnvironment: GLOBAL_CONSTANTS.MSTR_ENV_VARIABLE_NAME });

  let uiIframeModal;
  let currentMode;
  let authenticationDetails;

  const applyCustomEnvironmentEngine = () => { // function applying custom environment engine to the Jupyter
    INITIAL_ENGINE
      .setCustomEnvironmentEngine()
      .verifyCustomEnvironment();
  };

  window.debugMSTR = {
    JupyterCell,
    JupyterKernel,
    PythonCode,
    Utilities,
    initialEngine: INITIAL_ENGINE,
    applyCustomEnvironmentEngine,
    uiIframeModal: () => uiIframeModal,
  };

  // --- backward compatibility engine ---
  // [remove at the end of the year 2020]
  const refactoredEnvironments = [
    ...JSON.parse(localStorage.getItem('mstr_envs') || '[]'),
    ...JSON.parse(localStorage.getItem('mstr-environments') || '[]'),
  ];
  localStorage.removeItem('mstr_envs');
  localStorage.setItem('mstr-environments', JSON.stringify(refactoredEnvironments));
  const refactoredProjects = {
    ...JSON.parse(localStorage.getItem('mstr_projs') || '{}'),
    ...JSON.parse(localStorage.getItem('mstr-projects') || '{}'),
  };
  localStorage.removeItem('mstr_projs');
  localStorage.setItem('mstr-projects', JSON.stringify(refactoredProjects));
  // ---

  const listenerForCustomCellResponses = (event) => { // listener for Custom Cell Data Requests responses
    // eslint-disable-next-line no-unused-vars
    const { data: { responseType, responseDetails } } = event;

    // [PLACEHOLDER FOR FURTHER DEVELOPMENT]
  };

  const listenerForUiFunctionalities = (event) => { // main mstr listener for connection with UI functionalities
    const { backendManager } = window;

    const { data: { messageType, authInfo, dataframeDetails, otherDetails = {}, middlewareDetails, identityToken } } = event;
    const {
      initializeConnectorUi, updateEnvironmentsList, updateProjectsList, uiScreenChange,
      connectionDataUpdate, gatherDataframeContent, refreshExportDetails,
      createExportCell, createUpdateCell, createImportCell, applyDataframeChangesSteps,
    } = Utilities.messageTypes;

    otherDetails.customEnvironment = GLOBAL_CONSTANTS.MSTR_ENV_VARIABLE_NAME;

    authenticationDetails = { ...authenticationDetails, identityToken };

    switch (messageType) {
      // preparation and middleware update cases
      case initializeConnectorUi: {
        const iframeDocument = document.querySelector('iframe#mstr-iframe').contentWindow.document;
        Utilities.applyCustomStyleFile('ui-iframe.css', iframeDocument);

        const environments = localStorage.getItem('mstr-environments');
        const projects = localStorage.getItem('mstr-projects');

        environments && backendManager.addEnvToSuggestions(environments);
        projects && backendManager.addRecentProjects(projects);

        const { envName } = (authenticationDetails || {});
        const selectedProjectsList = projects && envName
          ? JSON.parse(projects)[envName] || []
          : [];

        if (currentMode !== 'authentication' && selectedProjectsList.length && authenticationDetails) {
          backendManager.automaticLogin(authenticationDetails, authenticationDetails.authToken, currentMode, selectedProjectsList);
        } else backendManager.showAuthenticationPage();

        // TODO: replace with package number computed from PythonCode.code.forGettingPackageVersionNumber
        const PACKAGE_VERSION_NUMBER = '11.2.2.1';
        backendManager.updatePackageVersionNumber(PACKAGE_VERSION_NUMBER);

        new JupyterKernel(Jupyter.notebook.kernel)
          .code(PythonCode.code.forGettingKernelInfo)
          .execute()
          .then((self) => {
            backendManager.updateBackendParameters(JSON.stringify(self.getResult()));
          });

        new JupyterKernel(Jupyter.notebook.kernel)
          .code(PythonCode.code.forGettingDataframesNames)
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
        //TODO: importing/exporting flag
        break;
      }
      case createImportCell: {
        uiIframeModal.modal('hide');
        new JupyterCell(Jupyter.notebook, authenticationDetails, dataframeDetails, otherDetails).forImport();
        //TODO: importing/exporting flag
        break;
      }
      case createUpdateCell: {
        uiIframeModal.modal('hide');
        new JupyterCell(Jupyter.notebook, authenticationDetails, dataframeDetails, otherDetails).forUpdate();
        //TODO: importing/exporting flag
        break;
      }

      // application of middleware changes / Jupyter kernell changes cases
      case applyDataframeChangesSteps: {
        const { steps, selectedDataframes } = otherDetails;

        new JupyterKernel(Jupyter.notebook.kernel, { customEnvironment: GLOBAL_CONSTANTS.MSTR_ENV_VARIABLE_NAME })
          .resetCustomEnvironment()
          .then((self) => {
            self.applySameOnEachElement(steps, (item, that) => {
              that
                .code(PythonCode.code.forApplyingStep, item)
                .shell()
                .execute();
            })
              .then(() => {
                const allColumnsSelections = selectedDataframes.map(({ dfName, selectedObjects }) => (
                  new JupyterKernel(Jupyter.notebook.kernel, { name: dfName, selectedObjects }, otherDetails)
                    .code(PythonCode.code.forDataframeColumnsSelection)
                    .shell()
                    .execute()
                ));
                JupyterKernel.resolveAll(allColumnsSelections).then(() => {
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
          .code(PythonCode.code.forGettingDataframeData)
          .execute()
          .then((self) => {
            finalOutput.content = self.getResult();
            self
              .code(PythonCode.code.forModelingGatheredData)
              .execute()
              .then((selfFinal) => {
                // clearing structure to copy RStudio output architecture
                const result = selfFinal.getResult();
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
          .code(PythonCode.code.forGettingDataframesNames)
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
        && event.source.document.location.pathname === GLOBAL_CONSTANTS.EXTENSION_PATHNAME;

      if (!isFromMstrConnector) {
        return;
      }

      const hasCorrectStructure = !!messageType || !!responseType;

      if (!hasCorrectStructure) {
        throw new Error('Incorrect window.postMessage() event structure');
      }

      applyCustomEnvironmentEngine();

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

  const buildMstr = () => ( // main function applying connection to UI
    $('<div id="mstr-container" />')
      .append(
        $('<iframe />')
          .attr({
            src: `${GLOBAL_CONSTANTS.CONNECTOR_ADDRESS}?loading=true`,
            id: 'mstr-iframe',
          }),
      )
  );

  const showMstrModal = () => { // function for displaying UI
    uiIframeModal = Dialog
      .modal({
        show: false,
        notebook: Jupyter.notebook,
        keyboard_manager: Jupyter.notebook.keyboard_manager,
        body: buildMstr(),
      })
      .attr('id', 'mstr-modal');

    uiIframeModal
      .on('shown.bs.modal', function () {
        $(this)
          .find('iframe#mstr-iframe')
          .focus();
      })
      .modal('show');
  };

  const initialize = () => { // MSTRIO extension initialization function
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
          src="${GLOBAL_CONSTANTS.ORIGIN}${GLOBAL_CONSTANTS.EXTENSION_MAIN_FOLDER}/mstr.ico"
          id="mstr-ico"
        >`,
      )
      .bind('keydown', function (event) {
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

  return {
    load_jupyter_extension: loadMstrExtensionToJupyter,
    load_ipython_extension: loadMstrExtensionToJupyter,
  };
});

define(['./python-code'], (PythonCode) => class JupyterKernel {
  constructor(kernel, ...args) {
    if (args.length) {
      if ('user' in args[0] || 'password' in args[0]) {
        [
          this.authenticationDetails,
          this.dataframeDetails,
          this.otherDetails,
        ] = args;
      } else if ('customEnvironment' in args[0]) {
        [this.otherDetails] = args;
      } else {
        [
          this.dataframeDetails,
          this.otherDetails,
        ] = args;
      }
    }

    this.kernel = kernel;
    this.getPythonCode = new PythonCode(...args);
    this.command = Promise.resolve({});
    this.result = {};
    this.codeString = '';
    this.shellOnly = false;
    this.showDebug = false;
  }


  // functions for main engine of the class
  debug = () => {
    this.showDebug = true;
    return this;
  }

  static resolveAll = (allJupyterKernelInstances) => {
    const allPromises = allJupyterKernelInstances.map(({ command }) => command);

    return Promise.all(allPromises);
  }

  properties = (callbackFunctions) => {
    const {
      shell = () => {}, // callback function fired after shell execution status is returned
      output = () => {}, // callback function fired after output for Output Cell is ready
      input = () => {}, // callback function fired when some input is required
    } = callbackFunctions;
    /* This is object related to Jupyter Kernel
    * When used as second argument in Jupyter.notebook.kernel.execute, you can control what happens with output of python code
    */
    return {
      shell: {
        reply: shell,
      },
      iopub: {
        output,
        clear_output: () => {},
      },
      input,
      clear_on_done: true,
    };
  }

  replyMessageTypes = { // docs: https://jupyter-client.readthedocs.io/en/stable/messaging.html
    // expected and wanted:
    stream: 'stream',
    executeResult: 'execute_result',

    // unexpected (no mstrio code should expect it):
    displayData: 'display_data',
    updateDisplayData: 'update_display_data',
    executeInput: 'execute_input',

    // erroneous:
    error: 'error',
  };

  get successReplies() {
    const { stream, executeResult } = this.replyMessageTypes;
    return [stream, executeResult];
  }

  replySuccessful = (reply) => this.successReplies.includes(reply);

  executePythonCodeInBackground = () => {
    const that = this;

    return (
      new Promise((resolve, reject) => {
        const solution = {
          code: that.codeString,
          shell: null,
        };

        const waitForAllCallbacks = (retryNumber = 0) => {
          retryNumber > 20 && reject(new Error('executePythonCodeInBackground timed out. Please retry.'));
          Object.values(solution).every((value) => value) && resolve(solution);
          setTimeout(waitForAllCallbacks, 50, retryNumber + 1);
        };

        const propertiesArgument = {
          shell: (out) => {
            solution.shell = out;
            this.shellOnly = false;
            if (out.msg_type === 'execute_reply' && out.content.status === 'ok') {
              that.showDebug && console.log('Successful resolution: ', solution);
              waitForAllCallbacks();
            } else { // reject overall
              reject(solution);
            }
          },
        };
        if (!that.shellOnly) {
          solution.output = null;
          propertiesArgument.output = (out) => {
            solution.output = out;
            solution.output.content.data.parsed = this.parseResult(solution);
          };
        }

        const props = that.properties(propertiesArgument);
        if (that.showDebug) {
          console.log(`CODE TO EXECUTE:\n${that.codeString}`);
          console.log('PROPERTIES FOR EXECUTION: ', props);
        }
        that.kernel.execute(that.codeString, props, { silent: false });
      })
    );
  };

  code = (input, ...args) => {
    /*
     * when providing the code for execution, you can access previous execution's output
     * by providing "input" as function with one parameter instead of straight string.
     * Then, the parameter will be previous execution's output.content.data["text/plain"] parsed with JSON.parse()
     */
    switch (typeof input) {
      case 'function':
        this.codeString = input(this.parseResult());
        break;
      case 'object':
        this.codeString = this.getPythonCode[input.name](...args);
        break;
      default: this.codeString = input;
    }
    if (typeof this.codeString !== 'string') {
      throw new Error('JupyterKernel error: code to execute is not in string format (cannot execute object as string)');
    }
    this.showDebug && console.log(`APPLIED CODE:\n${this.codeString}`);
    return this;
  }

  shell = () => {
    this.showDebug && console.log('APPLY ON SHELL ONLY');
    this.shellOnly = true;
    return this;
  }

  verifyCallbackType = (input) => {
    if (typeof input !== 'function') throw new Error('JupyterKernel syntax error: cannot fire not a function as callback');
  }

  execute = (_catchCallback) => {
    /* _catchCallback should expect one argument
     * param @error: reference to the error ouputted by executePythonCodeInBackground
     */
    const catchCallback = _catchCallback || ((error) => {
      error.code && console.warn(`CODE ERRORED:\n${error.code}`);
      console.error('JupyterKernel error: executePythonCodeInBackground threw an error: ', error);
    });
    this.verifyCallbackType(catchCallback);
    this.showDebug && !!_catchCallback && console.log('CUSTOM CATCH CALLBACK: ', catchCallback);
    this.command = this
      .executePythonCodeInBackground()
      .catch(catchCallback);
    this.showDebug && console.log('FRESH PROMISE IN EXECUTION: ', this.command);
    return this;
  }

  then = (callback) => {
    /* callback should expect two arguments
     * param @self: reference to the instance of this class
     * param @output: reference to the output = meaning kernel execution object
     */
    this.verifyCallbackType(callback);
    this.command
      .then((out) => {
        this.result = out;
        callback(this, out);
      });
    return this;
  }

  getResult = () => this.result.output.content.data.parsed || null;

  parseResult = (_forcedResult) => {
    const result = (_forcedResult || this.result).output;
    this.showDebug && console.log('RESULT TO PARSE: ', result);
    try {
      let output = result.content.data['text/plain'];
      output = output.replace(/'/gi, '"');
      output = output.replace(/\\\\"/ig, '\\"');
      output = output.replace(/\\\\\//ig, '/');
      const toParse = output.charAt(0) === '"' ? output.slice(1, -1) : output;
      const toReturn = JSON.parse(toParse);
      this.showDebug && console.log(`PARSED RESULT:\n${toReturn}`);
      return toReturn;
    } catch (err) {
      console.warn('JSON.parse() failed with this object: ', result);
      console.error(err);
      throw new Error('JupyterKernel error: result parsing failed');
    }
  }

  applySameOnEachElement = (iterableObject, callback) => {
    /* callback function should expect two arguments
     * param @item: reference to specific item in iterableObject
     * param @self: reference to instance of this class
     */
    this.verifyCallbackType(callback);
    iterableObject.forEach((item) => {
      this.then((self) => {
        callback(item, self);
      });
    });
    return this;
  }
  // ---


  setCustomEnvironmentEngine = () => {
    this.then((self) => {
      self
        .code(PythonCode.code.forInitialEngine)
        .shell()
        .execute(() => {});
    });
    return this;
  }

  resetCustomEnvironment = () => {
    const { customEnvironment } = this.otherDetails;
    this.then((self) => {
      self
        .code(`${customEnvironment} = create_custom_env()`)
        .shell()
        .execute(() => {});
    });
    return this;
  }

  updateCustomEnvironment = () => {
    const { customEnvironment } = this.otherDetails;
    this.then((self) => {
      self
        .code(`${customEnvironment} = update_custom_env()`)
        .shell()
        .execute(() => {});
    });
    return this;
  }

  verifyCustomEnvironment = () => {
    const { customEnvironment } = this.otherDetails;
    this
      .then((self) => {
        self
          .code((`
if '${customEnvironment}' in locals():
    ${customEnvironment} = update_custom_env()
else:
    ${customEnvironment} = create_custom_env()
          `).trim())
          .shell()
          .execute(() => {});
      });
    return this;
  }
});

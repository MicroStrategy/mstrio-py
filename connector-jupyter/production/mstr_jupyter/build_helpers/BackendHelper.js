import RStudioHelper from './RStudioHelper';
import JupyterHelper from './JupyterHelper';

const backend = 'Jupyter';
let backendHelper;

switch (backend) {
    case 'RStudio':
        backendHelper = new RStudioHelper();
        break;
    case 'Jupyter':
        backendHelper = new JupyterHelper();
        break;
    default:
        backendHelper = new RStudioHelper();
}

export {backend};
export default backendHelper;
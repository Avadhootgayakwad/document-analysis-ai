import { bootstrapApplication } from '@angular/platform-browser';

import { Workspace } from './app/workspace/workspace';

bootstrapApplication(Workspace)
  .catch(error => console.error(error));
//

interface Window {
  _paq: string[][];
}

declare module 'sgwt-account-center' {
  export interface IChangeEvent extends Event {
    detail: {
      language: string;
    }
  }

  export interface ISgwtAccountCenter extends HTMLElement {
    registerCallback(event: string, callback: Function): void;
  }
}

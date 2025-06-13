const GraphStyle = {
  node: {
    default: {
      shape: 'dot',
      size: 16,
      fixed: {
        x: false,
        y: false
      },
      color: {
        background: '#97C2FC',
        border: '#2B7CE9',
        highlight: {
          background: '#D2E5FF',
          border: '#2B7CE9'
        }
      },
      font: {
        color: '#343434',
        size: 14
      }
    },
    main: {
      color: {
        background: '#ff9900',
        border: '#cc6600',
        highlight: {
          background: '#ff9900',
          border: '#cc6600'
        }
      },
      font: {
        color: '#000000',
        size: 20
      }
    },
    connected: {
      color: {
        background: '#f39c12',
        border: '#d35400',
        highlight: {
          background: '#f39c12',
          border: '#d35400'
        }
      },
      font: {
        color: '#333333',
        size: 14
      }
    }
  },

  edge: {
    default: {
      color: {
        color: '#2B7CE9',
        highlight: '#2B7CE9',
        hover: '#2B7CE9'
      },
      width: 1
    },
    highlight: {
      color: {
        color: '#ff9900',
        highlight: '#cc6600',
        hover: '#cc6600'
      },
      width: 3
    }
  }
};

export default GraphStyle;

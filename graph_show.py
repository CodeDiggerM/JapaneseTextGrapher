# coding:utf-8

class GraphShow():
    """"Create demo page"""
    def __init__(self):
        self.base = '''
    <html>
    <head>
      <script type="text/javascript" src="VIS/dist/vis.js"></script>
      <link href="VIS/dist/vis.css" rel="stylesheet" type="text/css">
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    </head>
    <body>

    <div id="VIS_draw"></div>

    <script type="text/javascript">
      var nodes = data_nodes;
      var edges = data_edges;

      var container = document.getElementById("VIS_draw");

      var data = {
        nodes: nodes,
        edges: edges
      };

      var options = {
          nodes: {
              shape: 'circle',
              size: 15,
              font: {
                  size: 15
              }
          },
          edges: {
              font: {
                  size: 10,
                  align: 'center'
              },
              color: 'rgba(51,51,51,1)',
              arrows: {
                  to: {enabled: true, scaleFactor: 1.2}
              },
              smooth: {enabled: true}
          },
          physics: {
              enabled: true
          }
      };

      var network = new vis.Network(container, data, options);

    </script>
    </body>
    </html>
    '''

    def create_page(self, events):
        """Read data"""
        nodes = []
        for event in events:
            nodes.append(event[0])
            nodes.append(event[1])
        node_dict = {node[0]: (index, node[1]) for index, node in enumerate(nodes)}

        data_nodes = []
        data_edges = []
        for node, id_color in node_dict.items():
            data = {}
            data["group"] = 'Event'
            data["id"] = id_color[0]
            data["label"] = node
            data["color"] = id_color[1]
            data_nodes.append(data)

        for edge in events:
            data = {}
            data['from'] = node_dict.get(edge[0][0])[0]
            data['label'] = ''
            data['to'] = node_dict.get(edge[1][0])[0]
            data_edges.append(data)

        self.create_html(data_nodes, data_edges)
        return

    def create_html(self, data_nodes, data_edges):
        """Generate html file"""
        f = open('graph_show.html', 'w+')
        html = self.base.replace('data_nodes', str(data_nodes)).replace('data_edges', str(data_edges))
        f.write(html)
        f.close()

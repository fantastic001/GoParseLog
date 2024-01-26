import re
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF
import iso8601


class LogEntry:
    def __init__(self, level, timestamp, file, message):
        self.level = level
        self.timestamp = timestamp
        self.file = file
        self.message = message

    def __repr__(self):
        return f"{self.timestamp} [{self.level}] {self.file}: {self.message}"
    
    def __eq__(self, other):
        if isinstance(other, LogEntry):
            return (self.level == other.level and
                    self.timestamp == other.timestamp and
                    self.file == other.file and
                    self.message == other.message)
        return False

def parse_log_line(line):
    pattern = r'([IWEF])(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{6}) +(\d+) ([^:]+):(.+)'
    match = re.match(pattern, line.strip())
    if match:
        level, timestamp, _, file, message = match.groups()
        return LogEntry(level, timestamp, file, message)
    else:
        return None

def parse_glog_file(file_path):
    logs = []
    with open(file_path, 'r') as file:
        for line in file:
            entry = parse_log_line(line)
            if entry:
                logs.append(entry)
    return logs

def parse_context_message(logs):
    context_message_pattern = re.compile(r'([a-zA-Z0-9-]+): (.+)')
    context_messages = {}

    for log in logs:
        match = context_message_pattern.search(log.message)
        if match:
            context, message = match.groups()
            context_messages.setdefault(context, []).append(message)

    return context_messages

def create_rdf_from_logs(logs):
    # Namespace for our log entries
    LOG = Namespace("http://example.org/log/")

    # Sort the logs by timestamp
    sorted_logs = sorted(logs, key=lambda log: iso8601.parse_date(log.timestamp))

    # Create an RDF graph
    g = Graph()

    # Add triples for each consecutive log pair
    for i in range(len(sorted_logs) - 1):
        subj = URIRef(LOG[str(i)])
        pred = LOG.happenedBefore
        obj = URIRef(LOG[str(i + 1)])

        g.add((subj, pred, obj))

    return g

def get_logs_before(graph, base_log_uri):
    """
    Returns all log entries that happened before the given log entry.

    Args:
    - graph: An RDFlib Graph object containing the log entries and their relationships.
    - base_log_uri: The URI of the base log entry as a string.

    Returns:
    A list of URIs representing log entries that happened before the given log entry.
    """
    sparql_query = """
    PREFIX log: <http://example.org/log/>

    SELECT ?logEntry
    WHERE {
      ?logEntry log:happenedBefore+ <%s> .
    }
    """ % base_log_uri

    results = graph.query(sparql_query)
    return [str(row.logEntry) for row in results]



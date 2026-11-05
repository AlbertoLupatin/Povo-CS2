"""Cache immutable VMAP insertion state without changing serialized entities."""
import re
import threading

_NODE_IDS = r'"nodeID"\s+"int"\s+"(\d+)"'


class _EntityText(str):
    pass


def enable(project):
    """Install process-local fast point insertion; return stats and an undo call."""
    original_insert = project._insert_point_entity
    original_opening = project._world_children_opening
    original_re = project.re
    active = threading.local()
    stats = dict(insertions=0, cached_insertions=0, full_scans=0)

    class RegexProxy:
        def __getattr__(self, name):
            return getattr(original_re, name)

        def findall(self, pattern, text, *args, **kwargs):
            if getattr(active, 'inserting', False) and pattern == _NODE_IDS and isinstance(text, _EntityText) and not args and not kwargs:
                return [str(text.max_node_id)]
            return original_re.findall(pattern, text, *args, **kwargs)

    def opening(text):
        if isinstance(text, _EntityText):
            return text.children_opening
        return original_opening(text)

    def insert(text, token, classname, origin, properties=(), *, angles='0 0 0'):
        properties = tuple(properties)
        values = [classname, origin, angles, *(item for pair in properties for item in pair)]
        safe = all(not any(character in str(value) for character in ('"', '\\', '\n', '\r')) for value in values)
        if not safe:
            return original_insert(str(text), token, classname, origin, properties, angles=angles)
        if isinstance(text, _EntityText):
            cached = text
            stats['cached_insertions'] += 1
        else:
            cached = _EntityText(text)
            cached.max_node_id = max((int(value) for value in original_re.findall(_NODE_IDS, text)), default=1)
            cached.children_opening = original_opening(text)
            stats['full_scans'] += 1
        active.inserting = True
        try:
            result = original_insert(cached, token, classname, origin, properties, angles=angles)
        finally:
            active.inserting = False
        if result is cached:
            return result
        output = _EntityText(result)
        output.max_node_id = cached.max_node_id + 1
        output.children_opening = cached.children_opening
        stats['insertions'] += 1
        return output

    project.re = RegexProxy()
    project._world_children_opening = opening
    project._insert_point_entity = insert

    def undo():
        project.re = original_re
        project._world_children_opening = original_opening
        project._insert_point_entity = original_insert

    return stats, undo

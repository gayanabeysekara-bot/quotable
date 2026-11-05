"""ONVIF device discovery via WS-Discovery multicast probe (local network only).

Discovery only lists devices that answer the probe. It does not log in to cameras. Media
stream URL resolution via ONVIF GetStreamUri is not implemented in the MVP — enter the RTSP
URL shown in the camera's admin page instead.
"""

from __future__ import annotations

import socket
import uuid
import xml.etree.ElementTree as ET

MCAST = ("239.255.255.250", 3702)
PROBE = """<?xml version="1.0" encoding="UTF-8"?>
<e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"
 xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing"
 xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
 xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
 <e:Header><w:MessageID>uuid:{mid}</w:MessageID>
 <w:To e:mustUnderstand="true">urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>
 <w:Action e:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</w:Action></e:Header>
 <e:Body><d:Probe><d:Types>dn:NetworkVideoTransmitter</d:Types></d:Probe></e:Body>
</e:Envelope>"""

NS = {"d": "http://schemas.xmlsoap.org/ws/2005/04/discovery",
      "a": "http://schemas.xmlsoap.org/ws/2004/08/addressing"}


def parse_probe_match(xml: bytes) -> list[dict]:
    # Responses come from the local network; ElementTree does not resolve external entities.
    if len(xml) > 65536 or b"<!DOCTYPE" in xml or b"<!ENTITY" in xml:
        return []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    out = []
    for m in root.iter("{%s}ProbeMatch" % NS["d"]):
        xaddrs = (m.findtext("d:XAddrs", default="", namespaces=NS) or "").split()
        scopes = (m.findtext("d:Scopes", default="", namespaces=NS) or "").split()
        ep = m.find("a:EndpointReference/a:Address", NS)
        out.append({"xaddrs": xaddrs, "scopes": scopes, "endpoint": ep.text if ep is not None else ""})
    return out


def discover(timeout: float = 3.0) -> list[dict]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.settimeout(timeout)
    found: dict[str, dict] = {}
    try:
        sock.sendto(PROBE.format(mid=uuid.uuid4()).encode(), MCAST)
        while True:
            try:
                data, _addr = sock.recvfrom(65536)
            except socket.timeout:
                break
            for d in parse_probe_match(data):
                found[d["endpoint"] or ",".join(d["xaddrs"])] = d
    finally:
        sock.close()
    return list(found.values())

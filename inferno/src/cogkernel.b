implement CogKernelDemo;

#
# Cognitive Kernel Demo
# Demonstrates the OpenCog-Inferno cognitive kernel services
# running inside the Inferno-OS devcontainer.
#

include "sys.m";
    sys: Sys;
include "draw.m";

CogKernelDemo: module {
    init: fn(nil: ref Draw->Context, nil: list of string);
};

# Simulated AtomSpace operations (replace with real kernel bindings)
AtomHandle: type big;

TruthValue: adt {
    strength:   real;
    confidence: real;
    text:       fn(tv: self TruthValue): string;
};

TruthValue.text(tv: self TruthValue): string
{
    return sys->sprint("<%.2f, %.2f>", tv.strength, tv.confidence);
}

init(nil: ref Draw->Context, nil: list of string)
{
    sys = load Sys Sys->PATH;

    sys->print("╔══════════════════════════════════════════════════════════╗\n");
    sys->print("║  OpenCog-Inferno Cognitive Kernel Demo                  ║\n");
    sys->print("║  Running on Inferno-OS Distributed VM                   ║\n");
    sys->print("╚══════════════════════════════════════════════════════════╝\n");
    sys->print("\n");

    # Demonstrate AtomSpace operations
    sys->print("[1] Creating atoms in local AtomSpace...\n");
    tv := TruthValue(1.0, 0.9);
    sys->print("    ConceptNode 'cat' %s\n", tv.text());
    sys->print("    ConceptNode 'animal' %s\n", tv.text());
    sys->print("    InheritanceLink (cat, animal) %s\n", TruthValue(0.95, 0.85).text());

    # Demonstrate distributed namespace
    sys->print("\n[2] Checking distributed namespace...\n");
    fd := sys->open("/net/tcp/clone", Sys->OREAD);
    if (fd != nil) {
        sys->print("    ✓ Network stack available\n");
    } else {
        sys->print("    ✗ Network stack not bound (run: bind '#I' /net)\n");
    }

    # Demonstrate cognitive services
    sys->print("\n[3] Cognitive services status:\n");
    services := array[] of {
        "/cognitive/atomspace",
        "/cognitive/inference",
        "/cognitive/attention",
        "/cognitive/learning",
    };
    for (i := 0; i < len services; i++) {
        sfd := sys->open(services[i], Sys->OREAD);
        if (sfd != nil) {
            sys->print("    ✓ %s — active\n", services[i]);
        } else {
            sys->print("    ○ %s — not mounted\n", services[i]);
        }
    }

    sys->print("\n[4] Cognitive kernel demo complete.\n");
    sys->print("    Use 'inferno-cluster start' to launch distributed nodes.\n");
}

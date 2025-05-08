import QtQuick 2.15
import QtQuick.Particles 2.15

Rectangle {
    width: parent.width
    height: parent.height
    color: "transparent"

    ParticleSystem { id: sys }

    ImageParticle {
        system: sys
        source: "qrc:///particle.png"
        color: "#4a9eff"
        alpha: 0.6
    }

    Emitter {
        system: sys
        anchors.centerIn: parent
        emitRate: 100
        lifeSpan: 2000
        size: 16
        velocity: AngleDirection {
            angleVariation: 360
            magnitude: 100
            magnitudeVariation: 50
        }
    }
}
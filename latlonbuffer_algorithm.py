# -*- coding: utf-8 -*-

"""
/***************************************************************************
 latlonbuffer
                                 A QGIS plugin
 This plugin makes a buffer in meters around lat lon point features
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-10-31
        copyright            : (C) 2022 by Morten Sickel
        email                : morten@sickel.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Morten Sickel'
__date__ = '2022-10-31'
__copyright__ = '(C) 2022 by Morten Sickel'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeature,
                       QgsGeometry,
                       QgsPointXY,
                       QgsProject,
                       QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterFeatureSink)


class latlonbufferAlgorithm(QgsProcessingAlgorithm):
    """
    This algorithm makes a buffer given in meters around a potentially global point dataset in EPSG:4326.
    
    For each point, it defines a local crs as an azimuthal equal distance centered in the point. It then
    does the buffering in this crs before reprojecting the buffer to EPSG:4326. 
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It must be a point cover
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterDistance(
                'BUFFERDIST',
                self.tr('Buffer distance (meters)'),
                defaultValue = 100000,
                # Make distance units match the INPUT layer units:
                
            )
        )
        

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
                context, source.fields(), QgsWkbTypes.Polygon, source.sourceCrs())

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()
        # The newfeature is used as a basis for the buffering.
        newfeature = QgsFeature()
        # the point is set to 0,0, the crs will be defined later
        basepnt = QgsGeometry.fromPointXY(QgsPointXY(0,0))
        outcrs = QgsCoordinateReferenceSystem("EPSG:4326")
        bufferdist = self.parameterAsDouble(parameters, 'BUFFERDIST', context)
        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            attrs = feature.attributes()
            # makes a buffer with the right size in an undefined crs
            buffer = basepnt.buffer(bufferdist,5)
            # needs to find out where the point is to define the buffer's crs
            geom = feature.geometry()
            point = geom.asPoint()
            lat = point.y()
            lon = point.x()
            # defines the projection for the buffer and transforms it to EPSG:4326
            projstring = f"PROJ:+proj=aeqd +lat_0={lat} +lon_0={lon}"
            crs = QgsCoordinateReferenceSystem(projstring)
            xform = QgsCoordinateTransform(crs,outcrs,QgsProject.instance())
            buffer.transform(xform)
            newfeature.setGeometry(buffer)
            newfeature.setAttributes(attrs)
            # Add a feature in the sink
            sink.addFeature(newfeature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT: dest_id}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Buffer lat lon'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Algorithms for Vector layers'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return latlonbufferAlgorithm()
